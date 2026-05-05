import logging
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
        self._stopped = Event()

    def pause(self):
        logging.info(f"脚本已暂停: hwnd={self._hwnd}")
        self._running.set()

    def resume(self):
        logging.info(f"脚本已恢复: hwnd={self._hwnd}")
        self._running.clear()

    def stop(self):
        logging.info(f"脚本已停止: hwnd={self._hwnd}")
        self._stopped.set()
        self._running.set()

    def _wait_while_paused(self):
        while self._running.is_set() and not self._stopped.is_set():
            time.sleep(0.2)

    def _wait_for_task(self):
        while not self._running.is_set() and not self._stopped.is_set():
            task = js.get_execute_task(self._hwnd)
            if task is not None:
                logging.info(f"获取到待执行任务: {task['name']} v{task.get('version', '?')}")
                return task
            time.sleep(1)
        return None

    def run(self):
        while not self._stopped.is_set():
            self._wait_while_paused()
            if self._stopped.is_set():
                break
            task = self._wait_for_task()
            if task is not None:
                work = StaticCommon.get_task_config_by_id(task["id"])
                work["values"] = task.get("values", work.get("values", {}))
                logging.info(f"开始执行任务: {task['name']} v{task.get('version', '?')} | hwnd={self._hwnd}")
                engine = FlowEngine(
                    work=work,
                    hwnd=self._hwnd,
                    running=self._running
                )
                engine.loop()
                engine.start()
                engine.join()
