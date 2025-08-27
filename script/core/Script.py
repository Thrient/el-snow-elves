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
        self.__stopped = Lock()
        self.__finished = Event()
        self.__stop = Event()

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
        try:
            Utils.sendEmit(self.window, 'API:ADD:CHARACTER', state='初始化', hwnd=self.hwnd)
            self.windowConsole.setWindowNoMenu()
            # self.windowConsole.setWinEnableClickThrough()

            # 主任务处理循环，当finished标志未设置时持续运行
            while not self.__finished.is_set():
                try:
                    # 从任务调度器获取下一个待执行任务
                    task = self.taskScheduler.pop()
                    if task is None:
                        Utils.sendEmit(self.window, 'API:UPDATE:CHARACTER', state='无任务', hwnd=self.hwnd)
                        continue

                    # 发送任务状态更新信息
                    Utils.sendEmit(self.window, 'API:UPDATE:CHARACTER', state=task, hwnd=self.hwnd)

                    # 发送日志事件，记录任务开始信息
                    Utils.sendEmit(self.window, 'API:ADD:LOGS',
                                   time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                                   info="信息", data=f"{task}开始")

                    # 根据任务配置创建对应的任务对象实例
                    cls = TaskFactory.instance().create(self.taskConfig.model, task)
                    if cls is None:
                        continue
                    obj = cls(hwnd=self.hwnd, stopped=self.__stopped, finished=self.__finished, window=self.window,
                              taskConfig=self.taskConfig, windowConsole=self.windowConsole).instance()
                    obj.execute()
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

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
        self.__finished.set()
        self.windowConsole.restStyle()
        self.windowConsole.setWinUnEnableClickThrough()

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
        if not self.__stop.is_set():
            self.__stop.set()
            self.__stopped.acquire()
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
        if self.__stop.is_set():
            self.__stop.clear()
            self.__stopped.release()
        # 设置窗口控制台为可点击穿透状态
        self.windowConsole.setWinEnableClickThrough()

    def screenshot(self):
        """
        截取当前窗口的屏幕截图并保存为图片文件

        参数:
            self: 类实例对象，包含windowConsole属性用于窗口操作

        返回值:
            无返回值

        功能说明:
            1. 调用windowConsole的captureWindow方法获取窗口截图
            2. 将截图保存到临时图片目录，文件名为时间戳.bmp格式
        """
        image = self.windowConsole.captureWindow()
        # 保存截图到临时目录，使用时间戳作为文件名
        image.save(f"temp/images/{time.time()}.bmp")
