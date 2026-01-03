import logging
import time
from threading import Thread

from script.core.Scheduler import Scheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.TaskFactory import TaskFactory
from script.core.TaskScheduler import TaskScheduler
from script.state.ScriptState import ScriptState
from script.utils.Api import api
from script.utils.JsApi import js
from script.window.Console import Console
from script.window.WindowInteractor import WindowInteractor

logger = logging.getLogger(__name__)


class Script(Thread):
    def __init__(self, hwnd):
        super().__init__(daemon=True)
        self.hwnd = hwnd

        self._state = ScriptState.INIT

        # 组件
        self.taskScheduler = TaskScheduler(self.hwnd)
        self.winConsole: Console = Console(hwnd=self.hwnd)
        self.scheduler: Scheduler = Scheduler()

        # self.scheduler.sched.start()

    # 线程/进程安全的属性读写
    @property
    def state(self) -> ScriptState:
        return ScriptState(self._state)

    def _set_state(self, state: ScriptState):
        old = self.state
        self._state = state
        logger.debug("Script[%s] 状态变更 %s → %s", self.hwnd, old.name, state.name)

    def _is_state(self, *states: ScriptState) -> bool:
        return self.state in states

    def run(self):
        try:
            self._apply_initial_window_style()
            taskConfigScheduler.init(self.hwnd, "默认配置", {})
            self.taskScheduler.init(None)

            self._main_loop()
        except Exception as e:
            logger.exception("[HWND:%s] Script 线程异常崩溃: %s", self.hwnd, e)

    def _apply_initial_window_style(self):
        self.borderless()
        self.transparent(255)
        self.unlock()

    def _main_loop(self):
        while not self._is_state(ScriptState.UNBINDING):
            if not self._is_state(ScriptState.RUNNING, ScriptState.INIT, ScriptState.NOTASK):
                continue

            task = self.taskScheduler.pop()
            if task is None:
                if not self._is_state(ScriptState.NOTASK):
                    self._set_state(ScriptState.NOTASK)
                    self._update_character_state("无任务")
                time.sleep(1)
                continue
            self._set_state(ScriptState.RUNNING)
            self._execute_task(task)

    def _execute_task(self, task_name: str):
        self._update_character_state(task_name)
        self._log_task_start(task_name)

        try:
            cls = TaskFactory.instance().create(taskConfigScheduler.config[self.hwnd]["配置"].model, task_name)
            if cls is None:
                logger.warning("任务 %s 未注册或创建失败", task_name)
                return

            with cls(hwnd=self.hwnd) as obj:
                obj.execute()

        except Exception as e:
            logger.exception(f"执行任务 {task_name} 失败: {e}")

    def _update_character_state(self, state: str):
        js.emit("API:CHARACTERS:UPDATE", {"hwnd": self.hwnd, "state": state})

    @staticmethod
    def _log_task_start(task_name: str):
        js.emit("API:LOGS:ADD", {
            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "data": f"{task_name} 开始"
        })

    def launch(self, config, task, parameter):
        if not self._is_state(ScriptState.STOPPED, ScriptState.INIT):
            logger.info("[HWND:%s] 重复调用 launch，已忽略", self.hwnd)
            return

        self._set_state(ScriptState.RUNNING)
        self.lock()

        taskConfigScheduler.init(self.hwnd, config, parameter)
        self.taskScheduler.init(task)

    def end(self):
        self._set_state(ScriptState.STOPPED)
        self.unlock()
        self.taskScheduler.clear()
        api.emit(f"API:SCRIPT:TASK:END:{self.hwnd}")

    def stop(self):
        self._set_state(ScriptState.PAUSED)
        api.emit("API:SCRIPT:TASK:STOP")
        self.unlock()

    def resume(self):
        """恢复运行"""
        if self._is_state(ScriptState.PAUSED):
            self._set_state(ScriptState.RUNNING)
        elif self._is_state(ScriptState.FULLSCREEN):
            self._set_state(ScriptState.RUNNING)
            self.winConsole.restore_style()
        self.borderless()
        self.lock()
        api.emit("API:SCRIPT:TASK:RESUME")

    def lock(self):
        try:
            self.winConsole.enable_click_through()
        except Exception as e:
            logger.error("启用点击穿透失败: %s", e)

    def unlock(self):
        try:
            self.winConsole.disable_click_through()
        except Exception as e:
            logger.error("禁用点击穿透失败: %s", e)

    def reset_win(self):
        try:
            self.winConsole.restore_style()
        except Exception as e:
            logger.error("恢复窗口样式失败: %s", e)

    def borderless(self):
        try:
            self.winConsole.borderless()
        except Exception as e:
            logger.error("设置无边框失败: %s", e)

    def fullScreen(self):
        if self._is_state(ScriptState.FULLSCREEN):
            return
        self._set_state(ScriptState.FULLSCREEN)
        self.stop()
        try:
            self.winConsole.full_screen()
        except Exception as e:
            logger.error("进入全屏失败: %s", e)
            self._set_state(ScriptState.PAUSED)  # 回退

    def transparent(self, alpha: int):
        try:
            self.winConsole.set_transparent(alpha)
        except Exception as e:
            logger.error("设置透明度 %s失败: %s", e)

    def screenshot(self):
        try:
            image = WindowInteractor(self.hwnd).capture
            filename = f"temp/images/{time.time()}.bmp"
            image.save(filename)
            logger.info("截图保存 → %s", filename)
        except Exception as e:
            logger.error("截图失败: %s", e)

    def unbind(self):
        """彻底解绑并准备退出进程"""
        self._set_state(ScriptState.UNBINDING)
        self.taskScheduler.clear()
        api.emit(f"API:SCRIPT:TASK:END:{self.hwnd}")
        self.reset_win()
        self.unlock()
        self.transparent(255)
