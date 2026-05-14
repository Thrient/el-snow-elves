"""账号代理 — 基于mitmproxy的HTTPS代理，支持录制和注入"""

import asyncio
import json
import logging
import os
import socket
import sys
import subprocess
import threading
import time

from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
from script.account.HostsManager import LOGIN_DOMAINS, HostsManager

logging.getLogger("mitmproxy").setLevel(logging.ERROR)

# ---- DNS反回环：代理内部用硬编码IP，不走hosts劫持 ----
_TARGET_IPS = {
    "service.mkey.163.com": "42.186.193.21",
    "sdk-os.mpsdk.easebar.com": "8.222.80.103",
}
_resolved_ips = dict(_TARGET_IPS)
_original_getaddrinfo = socket.getaddrinfo


def _patched_getaddrinfo(host, port, *args, **kwargs):
    if isinstance(host, str) and host in _resolved_ips:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (_resolved_ips[host], port))]
    return _original_getaddrinfo(host, port, *args, **kwargs)


socket.getaddrinfo = _patched_getaddrinfo

# ---- 端口复用：避免 TIME_WAIT 导致 10048 ----
_original_socket_init = socket.socket.__init__


def _patched_socket_init(self, family=-1, type=-1, proto=-1, fileno=None):
    _original_socket_init(self, family, type, proto, fileno)
    if family == socket.AF_INET and type == socket.SOCK_STREAM:
        try:
            self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass


socket.socket.__init__ = _patched_socket_init

RECORDING = "recording"
INJECTION = "injection"
PROXY_PORT = 443


class _CompatAddon:
    """兼容模式 addon：根据 Host 头将请求路由到正确的上游服务器"""

    def __init__(self, domains):
        self.domains = set(domains)

    def request(self, flow):
        host = flow.request.host_header or flow.request.host
        if host in self.domains:
            flow.request.host = host
            flow.request.port = 443
            flow.request.scheme = "https"


class _RequestLogger:
    """记录所有经过代理的请求，用于诊断"""

    def __init__(self, domains):
        self.domains = set(domains)
        self._seen = set()

    def request(self, flow):
        host = flow.request.host
        path = flow.request.path.split("?")[0]
        key = f"{flow.request.method} {host}{path}"
        if key not in self._seen:
            self._seen.add(key)
            logging.info(f"[Proxy REQ] {key}")


class _DynamicAddon:
    """动态 addon：根据 proxy.mode 切换录制/注入行为"""

    def __init__(self, domains, proxy):
        self.domains = set(domains)
        self.proxy = proxy
        self._stopping = False

    def response(self, flow):
        host = flow.request.host
        if host not in self.domains:
            return
        path = flow.request.path.split("?")[0]
        mode = self.proxy.mode

        if mode == RECORDING:
            self._handle_recording(flow, host, path)
        elif mode == INJECTION:
            self._handle_injection(flow, path)

    def _handle_recording(self, flow, host, path):
        if self.proxy.completed:
            return
        if "/exchange_token" in path:
            try:
                data = json.loads(flow.response.content)

                # 注入 is_remember 延长 token 有效期（参考 idv-login NATIVE_SAVE）
                ext = data.get("ext_info")
                if isinstance(ext, dict):
                    ext["is_remember"] = True
                pc_ext = data.get("pc_ext") or data.get("pc_ext_info") or data.get("pcExtInfo")
                if isinstance(pc_ext, dict):
                    pc_ext["is_remember"] = True
                flow.response.content = json.dumps(data, ensure_ascii=False).encode()

                user = data.get("user", {})
                if user:
                    self.proxy._addon.captured = {"source": "exchange_token", "response_data": data}
                    self.proxy.completed = True
                    name = user.get("client_username", user.get("name", ""))
                    logging.info(f"[AccountProxy REC] 捕获登录信息 (is_remember): {name}")
            except Exception as e:
                logging.error(f"[AccountProxy REC] exchange_token解析失败: {e}")

    def _handle_injection(self, flow, path):
        if path == "/mpay/api/qrcode/query":
            try:
                data = json.loads(flow.response.content)
                data.setdefault("qrcode", {})["status"] = 2
                flow.response.content = json.dumps(data, ensure_ascii=False).encode()
                logging.info("[AccountProxy INJ] 伪造扫码状态")
            except Exception:
                pass
        elif "/exchange_token" in path:
            t = self.proxy.token_info or {}
            resp_data = t.get("response_data", {})
            if resp_data:
                flow.response.content = json.dumps(resp_data, ensure_ascii=False).encode()
                flow.response.status_code = 200
                self.proxy.completed = True
                HostsManager.restore()
                logging.info("[AccountProxy INJ] 注入exchange_token响应，已还原hosts")


# ---- 模块级单例 ----
_proxy_instance = None


def get_proxy() -> "AccountProxy":
    global _proxy_instance
    if not _proxy_instance or not _proxy_instance._master:
        _proxy_instance = AccountProxy(port=PROXY_PORT)
        _proxy_instance.start()
    return _proxy_instance


class AccountProxy:
    """基于mitmproxy的HTTPS账号代理"""

    CONF_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "mitmproxy-conf"
    )
    CA_CERT = os.path.join(CONF_DIR, "mitmproxy-ca-cert.pem")

    def __init__(self, port=None, mode=RECORDING, token_info=None):
        self.port = port or PROXY_PORT
        self.mode = mode
        self.token_info = token_info
        self._thread = None
        self._master = None
        self._addon = None
        self._loop = None
        self._ready = threading.Event()
        self._error = None
        self.completed = False

    @staticmethod
    def install_ca():
        """安装mitmproxy CA证书到Windows受信任根"""
        ca_cert = AccountProxy.CA_CERT
        if not os.path.exists(ca_cert):
            logging.warning(f"[AccountProxy] CA证书尚未生成: {ca_cert}")
            return False
        try:
            result = subprocess.run(
                ["certutil", "-addstore", "Root", ca_cert],
                capture_output=True, text=True,
                creationflags=0x08000000,
            )
            logging.info(f"[AccountProxy] CA安装: {result.stdout.strip()}")
            return True
        except Exception as e:
            logging.warning(f"[AccountProxy] CA安装失败: {e}")
            return False

    @property
    def captured(self):
        if self._addon and hasattr(self._addon, "captured"):
            return self._addon.captured
        return None

    @staticmethod
    def _port_free(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port)) != 0
        s.close()
        return result

    def start(self):
        # 等端口释放
        for _ in range(30):
            if self._port_free(self.port):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError(f"端口 {self.port} 被占用，无法启动")

        self._ready.clear()
        self._error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5):
            self.stop()
            raise RuntimeError(self._error or "代理启动超时")
        if self._error:
            self.stop()
            raise RuntimeError(self._error)

    def stop(self):
        if not self._master:
            return
        self._ready.clear()
        try:
            self._master.shutdown()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.stop()
            except Exception:
                pass
        self._master = None
        # 等端口真正释放
        for _ in range(20):
            if self._port_free(self.port):
                return
            time.sleep(0.1)
        self._master = None

    def _run(self):
        if sys.platform == "win32":
            self._loop = asyncio.SelectorEventLoop()
        else:
            self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._run_async())
        except Exception as e:
            self._error = str(e)
            logging.error(f"[AccountProxy] 运行出错: {e}")
        finally:
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass
            self._loop.close()

    async def _run_async(self):
        os.makedirs(self.CONF_DIR, exist_ok=True)
        default_domain = LOGIN_DOMAINS[0]

        opts = Options(
            listen_host="127.0.0.1",
            listen_port=self.port,
            confdir=self.CONF_DIR,
            ssl_insecure=True,
            http3=False,
            mode=[f"reverse:https://{default_domain}"],
        )

        self._master = DumpMaster(opts, with_dumper=False)

        for h in list(logging.getLogger().handlers):
            if "mitmproxy" in type(h).__module__:
                logging.getLogger().removeHandler(h)

        self._master.addons.add(_CompatAddon(LOGIN_DOMAINS))
        self._master.addons.add(_RequestLogger(LOGIN_DOMAINS))
        self._addon = _DynamicAddon(LOGIN_DOMAINS, self)
        self._master.addons.add(self._addon)

        self._ready.set()
        await self._master.run()
