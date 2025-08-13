import time
from threading import Thread, Lock, Event

from script.core.TaskFactory import TaskFactory
from script.core.TaskScheduler import TaskScheduler
from script.core.WindowConsole import WindowConsole
from script.utils.Utils import Utils


class Script(Thread):
    def __init__(self, hwnd, window, taskConfig):
        super().__init__()
        self.hwnd = hwnd
        self.window = window
        self.taskConfig = taskConfig
        self.taskScheduler = TaskScheduler(hwnd, taskConfig)
        self.windowConsole = WindowConsole(hwnd)
        self.stopped = Lock()
        self.finished = Event()
        self.stop = Event()

    def run(self):
        """
        运行主任务循环

        该方法负责初始化窗口状态，然后进入任务处理循环，不断从任务调度器中获取任务并执行。
        在循环过程中会通过Utils.sendEmit发送状态更新信息到指定窗口。

        参数:
            无

        返回值:
            无
        """
        Utils.sendEmit(self.window, 'API:UPDATE:CHARACTER', state='初始化', hwnd=self.hwnd)
        self.windowConsole.setWindowNoMenu()
        # self.windowConsole.setWinEnableClickThrough()

        # 主任务处理循环，当finished标志未设置时持续运行
        while not self.finished.is_set():
            # 从任务调度器获取下一个待执行任务
            task = self.taskScheduler.pop()
            if task is None:
                Utils.sendEmit(self.window, 'API:UPDATE:CHARACTER', state='无任务', hwnd=self.hwnd)
                continue

            # 发送任务状态更新信息
            Utils.sendEmit(self.window, 'API:UPDATE:CHARACTER', state=task, hwnd=self.hwnd)

            # 根据任务配置创建对应的任务对象实例
            cls = TaskFactory.instance().create(self.taskConfig.model, task)
            if cls is None:
                continue
            obj = cls(hwnd=self.hwnd, stopped=self.stopped, finished=self.finished)

    def unbind(self):
        """
        解除绑定操作

        该函数用于设置finished标志位，表示某个操作或任务已经完成。
        通常用于线程同步或资源清理等场景。

        参数:
            self: 对象实例

        返回值:
            无
        """
        self.finished.set()

    def stop(self):
        """
        停止当前脚本的运行

        该函数用于停止脚本的运行状态，通过设置停止标志位并获取停止信号量来实现。
        同时会调用窗口控制台方法取消窗口的点击穿透功能。

        参数:
            self: 对象实例

        返回值:
            无
        """
        # 如果停止标志位未被设置，则执行停止流程
        if not self.stop.is_set():
            self.stop.set()
            self.stopped.acquire()
        # 取消窗口的点击穿透功能
        self.windowConsole.setWinUnEnableClickThrough()

    def resume(self):
        """
        恢复函数，用于恢复脚本的运行状态

        该函数会检查停止标志，如果已设置则清除标志并释放停止信号量，
        同时设置窗口控制台为可点击穿透状态

        参数:
            无

        返回值:
            无
        """
        # 如果停止标志已设置，则清除停止标志并释放停止信号量
        if self.stop.is_set():
            self.stop.clear()
            self.stopped.release()
        # 设置窗口控制台为可点击穿透状态
        self.windowConsole.setWinEnableClickThrough()
