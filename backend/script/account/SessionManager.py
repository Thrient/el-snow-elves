"""回放/录制会话管理 — 从 App.py 抽出，纯逻辑零 UI"""

import logging
import subprocess
import threading

from script.account.AccountProxy import get_proxy, RECORDING, INJECTION
from script.account.AccountManager import AccountManager
from script.account.HostsManager import HostsManager


_session_instance = None


def get_session() -> "SessionManager":
    global _session_instance
    if _session_instance is None:
        _session_instance = SessionManager()
    return _session_instance


class SessionManager:
    """管理代理会话生命周期：录制、回放、状态轮询"""

    def __init__(self):
        self._proxy = None
        self._hosts_hijacked = False
        self._channel_done = False

    # ── 内部 ──

    def _ensure_proxy(self):
        self._proxy = get_proxy()
        self._proxy.reset()

    def _start_session(self, mode, name="", token_info=None):
        self._ensure_proxy()
        self._proxy.mode = mode
        self._proxy.token_info = token_info
        self._proxy.completed = False
        self._hosts_hijacked = HostsManager.hijack()
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, creationflags=0x08000000)
        mode_label = "录制" if mode == RECORDING else "回放"
        logging.info(f"[Session] 开始{mode_label}: {name}")

    # ── 官服扫码录制 ──

    def start_qr_recording(self, name):
        try:
            self._start_session(RECORDING, name)
            return {"status": "recording", "message": f"请在游戏中手动登录账号 '{name}'"}
        except Exception as e:
            logging.error(f"[Session] 启动录制失败: {e}")
            return {"error": str(e)}

    # ── 渠道录制 ──

    def start_channel_recording(self, name, channel):
        try:
            def _run():
                channel_auth = _record_channel(channel)
                if channel_auth:
                    AccountManager.save_account({"name": name, "channel_auth": channel_auth})
                    logging.info(f"[Session] 渠道账号已保存: {name} ({channel})")
                    self._channel_done = True
                else:
                    logging.warning(f"[Session] 渠道登录失败: {name} ({channel})")

            threading.Thread(target=_run, daemon=True).start()
            labels = {"vivo": "Vivo", "bilibili": "B站", "huawei": "华为", "qihu360": "360"}
            return {"status": "recording", "message": f"请在弹出窗口中登录{labels.get(channel, channel)}账号"}
        except Exception as e:
            logging.error(f"[Session] 启动渠道录制失败: {e}")
            return {"error": str(e)}

    # ── 停止录制 ──

    def stop_recording(self, name):
        if self._channel_done:
            self._channel_done = False
            return {"status": "done", "account": name}
        if not self._proxy:
            return {"error": "未在录制"}
        token = self._proxy.captured
        HostsManager.restore()
        self._hosts_hijacked = False
        self._proxy.completed = False
        if token:
            AccountManager.save_account({"name": name, "token_info": token})
            logging.info(f"[Session] 账号录制完成: {name}")
            return {"status": "done", "account": name}
        logging.warning(f"[Session] 录制未捕获到token: {name}")
        return {"error": "未捕获到登录凭证"}

    # ── 状态 ──

    def recording_status(self):
        if self._channel_done:
            return {"status": "done", "has_token": True}
        if self._proxy and self._hosts_hijacked:
            if self._proxy.completed:
                return {"status": "done", "has_token": bool(self._proxy.captured)}
            return {"status": "recording", "has_token": False}
        return {"status": "idle", "has_token": False}

    # ── 回放 ──

    def start_replay(self, account_name):
        account = AccountManager.get_account(account_name)
        if not account:
            return {"error": f"账号不存在: {account_name}"}

        token_info = account.get("token_info")
        channel_auth = account.get("channel_auth")

        if channel_auth and not token_info:
            try:
                self._start_session(INJECTION, account_name, token_info={"source": "channel", "channel_auth": channel_auth})
                self._proxy.channel_fake = True
                return {"status": "replaying", "message": f"正在回放「{account_name}」，请在游戏中触发登录"}
            except Exception as e:
                logging.error(f"[Session] 启动渠道回放失败: {e}")
                return {"error": str(e)}

        if not token_info:
            return {"error": "账号未包含登录凭证"}
        try:
            self._start_session(INJECTION, account_name, token_info=token_info)
            return {"status": "replaying", "message": f"正在回放「{account_name}」，请在游戏中触发登录"}
        except Exception as e:
            logging.error(f"[Session] 启动回放失败: {e}")
            return {"error": str(e)}

    def stop_replay(self):
        HostsManager.restore()
        self._hosts_hijacked = False
        if self._proxy:
            self._proxy.completed = False
        logging.debug("[Session] 回放停止")
        return {"status": "stopped"}


def _record_channel(channel: str) -> dict | None:
    """渠道录制分发：每个渠道在自己的模块里实现 record()"""
    if channel == "huawei":
        from script.account.channel.HuaweiChannel import record
        return record()
    if channel == "vivo":
        from script.account.channel.VivoChannel import record
        return record()
    if channel == "bilibili":
        from script.account.channel.BilibiliChannel import record
        return record()
    if channel == "qihu360":
        from script.account.channel.Qihu360Channel import record
        return record()
    logging.warning(f"[Session] 未支持的渠道录制: {channel}")
    return None
