import time
from multiprocessing import Process, Event

from script.core.SwitchCharacterScheduler import switchCharacterScheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.TaskFactory import TaskFactory
from script.core.TaskScheduler import taskScheduler
from script.utils.Api import api
from script.utils.QueueListener import QueueListener
from script.window.Console import Console


class Script(Process):
    def __init__(self, hwnd, queue):
        super().__init__()
        self.hwnd = hwnd
        self.queue = queue

        self.obj = None
        self.winConsole = None
        self.queueListener = None

        self._unbind = Event()
        self._started = Event()
        self._full = Event()

    def run(self):
        """运行主任务循环"""
        try:
            self.init()
            while not self._unbind.is_set():
                try:
                    task = taskScheduler.pop()
                    if task is None:
                        self.queueListener.emit(
                            {
                                "event": "JS:EMIT",
                                "args": (
                                    "API:UPDATE:CHARACTER",
                                    {
                                        "hwnd": self.hwnd,
                                        "state": "无任务"
                                    }
                                )
                            }
                        )
                        time.sleep(1)
                        continue
                    self.queueListener.emit(
                        {
                            "event": "JS:EMIT",
                            "args": (
                                "API:UPDATE:CHARACTER",
                                {
                                    "hwnd": self.hwnd,
                                    "state": task
                                }
                            )
                        }
                    )
                    self.queueListener.emit(
                        {
                            "event": "JS:EMIT",
                            "args": (
                                "API:ADD:LOGS",
                                {
                                    "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                                    "info": "信息",
                                    "data": f"{task}开始"
                                }
                            )
                        }
                    )
                    cls = TaskFactory.instance().create(taskConfigScheduler.common.model, task)
                    if cls is None:
                        continue
                    with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as self.obj:
                        self.obj.execute()

                except Exception as e:
                    self.queueListener.emit(
                        {
                            "event": "JS:EMIT",
                            "args": (
                                "API:ADD:LOGS",
                                {
                                    "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                                    "info": "错误",
                                    "data": e
                                }
                            )
                        }
                    )
        except Exception as e:
            self.queueListener.emit(
                {
                    "event": "JS:EMIT",
                    "args": (
                        "API:ADD:LOGS",
                        {
                            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            "info": "错误",
                            "data": e
                        }
                    )
                }
            )

    def init(self):
        """初始化"""
        self.winConsole = Console(hwnd=self.hwnd)
        self.queueListener = QueueListener(self.queue, self.hwnd, "script")

        api.on("API:SCRIPT:STOP", self.stop)
        api.on("API:SCRIPT:RESUME", self.resume)
        api.on("API:SCRIPT:LOCK", self.lock)
        api.on("API:SCRIPT:UNLOCK", self.unlock)
        api.on("API:SCRIPT:FULLSCREEN", self.fullScreen)
        api.on("API:SCRIPT:TRANSPARENT", self.transparent)
        api.on("API:SCRIPT:SCREENSHOT", self.screenshot)
        api.on("API:SCRIPT:END", self.end)

        api.on("API:SCRIPT:UNBIND", self.unbind)
        api.on("API:SCRIPT:LAUNCH", self.launch)

        self.borderless()
        self.transparent(255)

        self.queueListener.start()

    def launch(self, config, kwargs):
        """启动"""
        if self._started.is_set():
            return
        self._started.set()
        self.lock()
        taskConfigScheduler.init(config, **kwargs)
        switchCharacterScheduler.reset()

    def lock(self):
        """锁定当前窗口"""
        try:
            self.winConsole.enable_click_through()
        except Exception as e:
            print(e)

    def unlock(self):
        """解锁当前窗口="""
        try:
            self.winConsole.disable_click_through()
        except Exception as e:
            print(e)

    def reset_win(self):
        try:
            self.winConsole.rest_style()
        except Exception as e:
            print(e)

    def borderless(self):
        try:
            self.winConsole.set_style_no_menu()
        except Exception as e:
            print(e)

    def fullScreen(self):
        """全屏窗口"""
        try:
            if self._full.is_set():
                return
            self._full.set()
            self.stop()
            self.winConsole.full_screen()
        except Exception as e:
            print(e)

    def transparent(self, transparent):
        """设置窗口透明度"""
        try:
            self.winConsole.set_transparent(transparent)
        except Exception as e:
            print(e)

    def stop(self):
        """停止脚本运行"""
        try:
            self.obj.stop()
        except Exception as e:
            print(e)
        finally:
            # 恢复原本窗口
            self.reset_win()
            # 取消窗口的点击穿透功能
            self.unlock()

    def resume(self):
        """恢复脚本运行"""
        try:
            self.obj.resume()
        except Exception as e:
            print(e)
        finally:
            self._full.clear()
            # 去除窗口菜单
            self.borderless()
            # 设置窗口控制台为可点击穿透状态
            self.unlock()

    def unbind(self):
        """解绑"""
        try:
            self.queueListener.end()
            taskScheduler.clear()
            self.obj.finish()
        except Exception as e:
            print(e)
        finally:
            self.reset_win()
            self.unlock()
            self.transparent(255)
            self._unbind.set()

    def end(self):
        try:
            taskScheduler.clear()
            self.obj.finish()
        except Exception as e:
            print(e)
        finally:
            self.unlock()
            self._started.clear()

    def screenshot(self):
        """截图并保存为图片文件"""
        image = self.winConsole.capture
        # 保存截图到临时目录，使用时间戳作为文件名
        image.save(f"temp/images/{time.time()}.bmp")
