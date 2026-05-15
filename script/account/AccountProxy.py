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


def _create_handler(proxy: "AccountProxy", router: "ProxyRouter"):
    """工厂：根据 proxy.mode + proxy.channel_fake 创建对应 handler（懒导入避免循环引用）"""
    if proxy.mode == RECORDING:
        from script.account.handler.QrScanRecordHandler import QrScanRecordHandler
        return QrScanRecordHandler(proxy, router)

    if proxy.mode == INJECTION:
        if proxy.channel_fake:
            ti = proxy.token_info or {}
            ct = (ti.get("channel_auth", {})).get("channel_type", "")

            if ct == "huawei":
                from script.account.handler.HuaweiReplayHandler import HuaweiReplayHandler
                return HuaweiReplayHandler(proxy, router)
            if ct in ("vivo", "nearme_vivo"):
                from script.account.handler.VivoReplayHandler import VivoReplayHandler
                return VivoReplayHandler(proxy, router)
            if ct == "bilibili":
                from script.account.handler.BilibiliReplayHandler import BilibiliReplayHandler
                return BilibiliReplayHandler(proxy, router)

            logging.warning(f"[Proxy] 未支持的渠道回放类型: {ct}")
            return None

        from script.account.handler.QrScanReplayHandler import QrScanReplayHandler
        return QrScanReplayHandler(proxy, router)

    return None


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


class ProxyRouter:
    """将代理事件路由到对应 handler。只做基础设施（提取 ID、Cookie 累积），
    录制/回放/渠道逻辑全在 handler 中。"""

    def __init__(self, domains, proxy):
        self.domains = set(domains)
        self.proxy = proxy
        self._cookie_jar: list[str] = []
        self._delayed_stop: threading.Timer | None = None
        self.captured: dict | None = None
        self._handler_cache: dict = {}

    # ── 供 handler 调用的公共 API ──

    @property
    def cookies(self) -> list[str]:
        return list(self._cookie_jar)

    def schedule(self, callback, delay: float = 3.0):
        if self._delayed_stop:
            self._delayed_stop.cancel()
        self._delayed_stop = threading.Timer(delay, callback)
        self._delayed_stop.start()

    def reset(self):
        if self._delayed_stop:
            self._delayed_stop.cancel()
            self._delayed_stop = None
        self._cookie_jar.clear()
        self.captured = None
        self._handler_cache.clear()

    # ── internal ──

    def _get_handler(self):
        key = (self.proxy.mode, self.proxy.channel_fake)
        if key not in self._handler_cache:
            h = _create_handler(self.proxy, self)
            if h:
                self._handler_cache[key] = h
            return h
        return self._handler_cache[key]

    # ── mitmproxy addon 接口 ──

    def request(self, flow):
        host = flow.request.host
        if host not in self.domains:
            return
        path = flow.request.path.split("?")[0]
        if "/qrcode/create_login" in path:
            self.proxy.game_id = flow.request.query.get("game_id", "")
            self.proxy.process_id = flow.request.query.get("process_id", "")
            logging.info(f"[Proxy] 提取 game_id={self.proxy.game_id} process_id={self.proxy.process_id}")

    def response(self, flow):
        host = flow.request.host
        if host not in self.domains:
            return
        path = flow.request.path.split("?")[0]

        # create_login 响应：提取 scanner_uuid，然后交给 handler
        if "/qrcode/create_login" in path:
            self._extract_scanner_uuid(flow)
            handler = self._get_handler()
            if handler:
                handler.on_create_login_response(flow)
            return

        # 录制模式下始终累积 Cookie
        if self.proxy.mode == RECORDING:
            self._capture_cookies(flow)

        handler = self._get_handler()
        if not handler:
            return

        if "/qrcode/query" in path:
            handler.on_qrcode_query(flow)
        elif "/exchange_token" in path:
            handler.on_exchange_token(flow)

    def _extract_scanner_uuid(self, flow):
        try:
            data = json.loads(flow.response.content)
            scanners = data.get("qrcode_scanners") or []
            if scanners:
                logging.info(f"[Proxy] scanner keys: {list(scanners[0].keys())}")
            top = {k: v for k, v in data.items() if k != "qrcode_scanners"}
            logging.info(f"[Proxy] create_login top keys: {list(top.keys())}")
            for k in ("uuid", "login_info", "qrcode_uuid", "qrcode_id"):
                if data.get(k):
                    self.proxy.scanner_uuid = str(data[k])
                    logging.info(f"[Proxy] found scanner_uuid from {k}: {self.proxy.scanner_uuid}")
                    break
        except Exception:
            pass

    def _capture_cookies(self, flow):
        for key, value in flow.response.headers.items(multi=True):
            if key.lower() == "set-cookie" and value not in self._cookie_jar:
                self._cookie_jar.append(value)


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
        self.game_id: str = ""
        self.channel_fake: bool = False
        self.channel_done: bool = False
        self.scanner_uuid: str = ""
        self.process_id: str = ""

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
        if self._addon:
            return self._addon.captured
        return None

    def reset(self):
        """重置所有会话状态标志"""
        self.completed = False
        self.game_id = ""
        self.process_id = ""
        self.channel_fake = False
        self.channel_done = False
        self.scanner_uuid = ""
        if self._addon:
            self._addon.reset()

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
        self._addon = ProxyRouter(LOGIN_DOMAINS, self)
        self._master.addons.add(self._addon)

        self._ready.set()
        await self._master.run()
