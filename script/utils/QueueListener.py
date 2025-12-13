import logging
import queue
import time
from threading import Thread, Event

from script.utils.Api import api

logger = logging.getLogger(__name__)


class QueueListener(Thread):
    def __init__(self, queue, hwnd, sign, daemon: bool = True):
        """初始化队列监听器
        """
        super().__init__(daemon=daemon)
        self.hwnd = hwnd
        self.sign = sign
        self.queue = queue

        self._stop_event = Event()

    def emit(self, data: dict) -> None:
        """主动向外发送消息（Script → 主进程/前端）"""
        try:
            payload = {**data, "sign": self.sign}
            self.queue.put(payload)
        except Exception as e:
            logger.error("[QueueListener:%s] emit 失败: %s", self.hwnd, e)

    def terminate(self) -> None:
        """优雅停止监听线程"""
        self._stop_event.set()

    def run(self) -> None:
        """主循环：高效、零延迟、无死循环"""
        logger.debug("[QueueListener:%s] 启动", self.hwnd)

        while not self._stop_event.is_set():
            try:
                # timeout 越小越灵敏，推荐 0.1~0.3
                msg = self.queue.get(timeout=0.2)

                # 1. 属于自己的消息 → 放回去，Script 主进程会处理（比如前端发来的控制命令）
                if msg.get("sign") == self.sign:
                    self.queue.put(msg)
                    time.sleep(0.5)
                    continue

                # 2. 其他进程的消息 → 直接转发给全局事件总线
                event_name = msg.get("event")
                args = msg.get("args", ())

                if not event_name:
                    continue

                # 异步投递，避免阻塞队列线程
                try:
                    api.emit(event_name, *args)
                except Exception as e:
                    logger.error("[QueueListener:%s] api.emit 异常 %s: %s", self.hwnd, event_name, e)

            except queue.Empty:
                continue
            except Exception as e:
                # 防止未知异常导致线程死亡
                logger.exception("[QueueListener:%s] 未预期异常: %s", self.hwnd, e)
                # 短暂休眠防止异常风暴
                self._stop_event.wait(1)

        logger.debug("[QueueListener:%s] 已停止", self.hwnd)
