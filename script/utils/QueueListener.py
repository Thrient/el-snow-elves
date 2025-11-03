import time
from threading import Thread, Event

from script.utils.Api import api


class QueueListener(Thread):
    def __init__(self, queue, hwnd, sign, daemon: bool = True):
        """初始化队列监听器
        """
        super().__init__(daemon=daemon)
        self._end = Event()
        self.hwnd = hwnd
        self._sign = sign
        self._queue = queue

    def end(self):
        """结束监听"""
        self._end.set()

    def emit(self, msg):
        """发送信息"""
        self._queue.put({**msg, "sign": self._sign})

    def run(self):
        """线程运行方法，持续监听队列消息"""
        while not self._end.is_set():
            try:
                msg = self._queue.get(block=True, timeout=0.5)
                if msg["sign"] == self._sign:
                    self._queue.put(msg)
                    time.sleep(1)
                    continue
                api.emit(msg["event"], *msg["args"])
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break
