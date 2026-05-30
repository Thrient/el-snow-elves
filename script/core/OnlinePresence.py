"""在线状态 — SSE 长连接，向 Hub 报告桌面端在线"""
import logging
import threading
import time
import requests

_log = logging.getLogger("Elves.OnlinePresence")

HUB_URL = "https://elves.elarion.cn/api/v1"
SSE_URL = f"{HUB_URL}/client/stream"
RECONNECT_DELAY = 15


class OnlinePresence:
    """后台线程维护到 Hub 的 SSE 长连接，断开自动重连"""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._response: requests.Response | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="online-presence")
        self._thread.start()
        _log.info("在线状态上报已启动")

    def stop(self):
        self._stop_event.set()
        if self._response:
            try:
                self._response.close()
            except Exception:
                pass
        # join 会阻塞，但 _response.close() 应秒级生效；设置较短超时避免卡死
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        _log.info("在线状态上报已停止")

    def _run(self):
        session = requests.Session()
        session.headers["Connection"] = "keep-alive"
        while not self._stop_event.is_set():
            try:
                _log.info(f"连接 SSE: {SSE_URL}")
                resp = session.get(SSE_URL, stream=True, timeout=(10, None))
                self._response = resp
                resp.raise_for_status()
                _log.info("SSE 已连接，开始接收心跳")
                for _line in resp.iter_lines(decode_unicode=True):
                    if self._stop_event.is_set():
                        resp.close()
                        return
                _log.warning("SSE 流结束，将重连")
            except Exception as e:
                if not self._stop_event.is_set():
                    _log.error(f"SSE 连接异常: {e}")
            finally:
                self._response = None
                try:
                    resp.close()
                except Exception:
                    pass
            for _ in range(RECONNECT_DELAY):
                if self._stop_event.is_set():
                    return
                time.sleep(1)


# 单例
presence = OnlinePresence()
