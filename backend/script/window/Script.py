import logging
import time
from threading import Thread, Event

from script.api.JsApi import js
from script.engine.FlowEngine import FlowEngine
from script.task import get_repo


class Script(Thread):
    def __init__(self, hwnd):
        super().__init__(daemon=True)
        self._hwnd = hwnd
        self._paused = Event()
        self._stopped = Event()

    def pause(self):
        logging.info(f"脚本已暂停: hwnd={self._hwnd}")
        self._paused.set()

    def resume(self):
        logging.info(f"脚本已恢复: hwnd={self._hwnd}")
        self._paused.clear()

    def stop(self):
        logging.info(f"脚本已停止: hwnd={self._hwnd}")
        self._stopped.set()
        self._paused.set()

    def skip_current(self):
        """跳过当前任务，自动继续下一个"""
        logging.info(f"跳过当前任务: hwnd={self._hwnd}")
        self._paused.set()

    def _wait_while_paused(self):
        while self._paused.is_set() and not self._stopped.is_set():
            time.sleep(0.2)

    def _wait_for_task(self):
        while not self._paused.is_set() and not self._stopped.is_set():
            task = js.get_execute_task(self._hwnd)
            if task is not None:
                ver = task.get('version')
                logging.info(f"获取到待执行任务: {task['name']} v{ver}" if ver else f"获取到待执行任务: {task['name']} (最新)")
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
                task_name = task.get("taskName") or task.get("name")
                task_version = task.get("version") or None
                repo = get_repo()
                tid, work = repo.resolve(task_name, task_version)
                if work is None:
                    logging.error(f"任务解析失败: name={task_name} version={task_version}")
                    continue
                work["values"] = task.get("values", work.get("values", {}))
                work["valueTypes"] = task.get("valueTypes", work.get("valueTypes", {}))
                debug_start = task.get("debugStart")
                debug_single = task.get("debugSingle", False)
                logging.info(f"开始执行任务: {task['name']} v{task.get('version', '?')} | hwnd={self._hwnd}" +
                             (f" | debug 起始={debug_start}" if debug_start else "") +
                             (" | 单步" if debug_single else ""))
                engine_kwargs = dict(work=work, hwnd=self._hwnd, paused=self._paused)
                if debug_start:
                    engine_kwargs["start"] = debug_start
                if debug_single:
                    engine_kwargs["single_step"] = True
                engine = FlowEngine(**engine_kwargs)
                if not debug_single:
                    engine.loop()
                engine.start()
                engine.join()
                engine.cleanup()
                # 如果是 skip_current 触发的暂停，自动恢复继续下一个任务
                if self._paused.is_set() and not self._stopped.is_set():
                    self._paused.clear()
