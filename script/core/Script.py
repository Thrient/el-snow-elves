import logging
import time
from multiprocessing import Process, Value
from typing import Optional

from script.core.Scheduler import Scheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.TaskFactory import TaskFactory
from script.core.TaskScheduler import taskScheduler
from script.state.ScriptState import ScriptState
from script.utils.Api import api
from script.utils.QueueListener import QueueListener
from script.window.Console import Console

logger = logging.getLogger(__name__)


class Script(Process):
    def __init__(self, hwnd, queue):
        super().__init__(daemon=True)
        self.hwnd = hwnd
        self.queue = queue

        self._state = Value('i', ScriptState.INIT.value)

        # 组件
        self.winConsole: Optional[Console] = None
        self.queueListener: Optional[QueueListener] = None
        self.scheduler: Optional[Scheduler] = None

    # 线程/进程安全的属性读写
    @property
    def state(self) -> ScriptState:
        return ScriptState(self._state.value)

    def _set_state(self, state: ScriptState):
        old = self.state
        self._state.value = state.value
        logger.debug("Script[%s] 状态变更 %s → %s", self.hwnd, old.name, state.name)

    def _is_state(self, *states: ScriptState) -> bool:
        return self.state in states

    def run(self) -> None:
        try:
            self._initialize_components()
            self._register_events()
            self._apply_initial_window_style()

            api.emit("TASK:SCHEDULER:INIT")
            self._main_loop()

        except Exception as e:
            logger.exception("[HWND:%s] Script 进程异常崩溃: %s", self.hwnd, e)

    def _initialize_components(self):
        self.winConsole = Console(hwnd=self.hwnd)
        self.queueListener = QueueListener(self.queue, self.hwnd, "script")
        self.scheduler = Scheduler(queueListener=self.queueListener)

        self.queueListener.start()
        self.scheduler.sched.start()

    def _register_events(self):
        # === 1. 生命周期控制（核心） ===
        api.on("API:SCRIPT:LAUNCH", self.launch)  # 启动整个脚本进程
        api.on("API:SCRIPT:END", self.end)  # 结束脚本（停止任务）
        api.on("API:SCRIPT:UNBIND", self.unbind)  # 彻底解绑并退出进程

        # === 2. 运行状态切换 ===
        api.on("API:SCRIPT:STOP", self.stop)  # 暂停（玩家要手动操作）
        api.on("API:SCRIPT:RESUME", self.resume)  # 恢复自动运行

        # === 3. 窗口交互控制 ===
        api.on("API:SCRIPT:LOCK", self.lock)  # 启用点击穿透
        api.on("API:SCRIPT:UNLOCK", self.unlock)  # 禁用点击穿透
        api.on("API:SCRIPT:FULLSCREEN", self.fullScreen)  # 进入全屏
        api.on("API:SCRIPT:TRANSPARENT", self.transparent)  # 设置透明度

        # === 4. 辅助工具 ===
        api.on("API:SCRIPT:SCREENSHOT", self.screenshot)  # 手动截图

    def _apply_initial_window_style(self):
        self.borderless()
        self.transparent(255)
        self.unlock()

    def _main_loop(self):
        while not self._is_state(ScriptState.UNBINDING):
            if not self._is_state(ScriptState.RUNNING, ScriptState.INIT):
                time.sleep(0.5)
                continue

            task = taskScheduler.pop()
            if task is None:
                self._update_character_state("无任务")
                time.sleep(0.5)
                continue

            self._execute_task(task)

    def _execute_task(self, task_name: str):
        self._update_character_state(task_name)
        self._log_task_start(task_name)

        try:
            task_instance = TaskFactory.instance().create(taskConfigScheduler.common.model, task_name)
            if task_instance is None:
                logger.warning("任务 %s 未注册或创建失败", task_name)
                return

            with task_instance(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
                obj.execute()

        except Exception as e:
            logger.exception(f"执行任务 {task_name} 失败: {e}")

    def _update_character_state(self, state: str):
        self.queueListener.emit({
            "event": "JS:EMIT",
            "args": ("API:CHARACTERS:UPDATE", {"hwnd": self.hwnd, "state": state})
        })

    def _log_task_start(self, task_name: str):
        self.queueListener.emit({
            "event": "JS:EMIT",
            "args": ("API:LOGS:ADD", {
                "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "data": f"{task_name} 开始"
            })
        })

    def launch(self, config, task, parameter):
        if not self._is_state(ScriptState.STOPPED, ScriptState.INIT):
            logger.info("[HWND:%s] 重复调用 launch，已忽略", self.hwnd)
            return

        self._set_state(ScriptState.RUNNING)
        self.lock()

        api.emit("TASK:CONFIG:SCHEDULER:INIT", config, parameter)
        api.emit("SWITCH:CHARACTER:SCHEDULER:CLEAR")
        api.emit("TASK:SCHEDULER:INIT", task)

    def end(self):
        self._set_state(ScriptState.STOPPED)
        self.unlock()
        api.emit("TASK:SCHEDULER:CLEAR")
        api.emit("API:SCRIPT:TASK:FINISH")

    def stop(self):
        self._set_state(ScriptState.PAUSED)
        api.emit("API:SCRIPT:TASK:STOP")
        self.reset_win()
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
            image = self.winConsole.capture
            if not image:
                return
            filename = f"temp/images/{time.time()}.bmp"
            image.save(filename)
            logger.info("截图保存 → %s", filename)
        except Exception as e:
            logger.error("截图失败: %s", e)

    def unbind(self):
        """彻底解绑并准备退出进程"""
        self._set_state(ScriptState.UNBINDING)
        api.emit("TASK:SCHEDULER:CLEAR")
        api.emit("API:SCRIPT:TASK:FINISH")
        self.reset_win()
        self.unlock()
        self.transparent(255)
