import time
from threading import Thread, Event

from script.api.JsApi import js
from script.core.FlowEngine import FlowEngine
from script.core.StaticCommon import StaticCommon


class Script(Thread):
    def __init__(self, hwnd):
        super().__init__(daemon=True)
        self._hwnd = hwnd
        self._running = Event()

    def pause(self):
        """暂停任务"""
        self._running.set()

    def resume(self):
        """恢复（继续）执行"""
        self._running.clear()

    def _wait_while_paused(self):
        while self._running.is_set():
            time.sleep(0.2)

    def _wait_for_task(self):
        while not self._running.is_set():
            task = js.get_execute_task(self._hwnd)
            print(task)
            if task is not None:
                return task
            time.sleep(1)
        return None

    def run(self):
        """执行脚本主循环"""
        while True:
            self._wait_while_paused()
            task = self._wait_for_task()
            if task is not None:
                work = StaticCommon.get_task_config_by_id(task["id"])
                work["values"] = task.get("values", work.get("values", {}))
                engine = FlowEngine(
                    work=work,
                    hwnd=self._hwnd,
                    running=self._running
                )
                engine.loop()
                engine.start()
                engine.join()
