import logging
import random
import time
from abc import ABC, abstractmethod
from threading import Lock, Event

from airtest.aircv.utils import pil_2_cv2
from airtest.core.cv import Template

from script.config.Config import Config
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.Timer import Timer
from script.functools.functools import delay, repeat, during, verify


class BasisTask(ABC):
    def __init__(self, hwnd, winConsole, queueListener):
        super().__init__()
        self.hwnd = hwnd
        self.winConsole = winConsole
        self.queueListener = queueListener
        self._stopped = Lock()
        self._finished = Event()
        self.taskConfig = taskConfigScheduler.config

        self.timer = Timer()
        # 流程控制变量, 默认值1
        self._setup = 1
        # 事件变量字典
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    @property
    def setup(self):
        return self._setup

    @setup.setter
    def setup(self, state):
        if state == self._setup:
            return
        self._reset_state_variables(state)
        self._setup = state

    def _reset_state_variables(self, state):
        """重置变量"""
        reset_config = self.state_reset_config.get(state, {})
        for var_name, value in reset_config.items():
            if var_name not in self.event:
                continue
            self.event[var_name] = value() if callable(value) else value

    def stop(self):
        """暂停"""
        self._stopped.acquire()
        self.timer.stop()

    def resume(self):
        """恢复"""
        try:
            self.timer.resume()
            self._stopped.release()
        except Exception as e:
            print(e)

    def finish(self):
        """结束"""
        self.resume()
        self._finished.set()

    @abstractmethod
    def instance(self):
        """
        抽象静态方法，用于获取类的实例对象

        该方法是一个抽象方法，需要在子类中实现具体的实例化逻辑。
        通常用于实现单例模式或其他实例管理机制。

        Returns:
            返回类的实例对象，具体类型取决于子类的实现
        """
        pass

    @abstractmethod
    def execute(self):
        """
        执行方法的抽象定义

        该方法是一个抽象方法，需要在子类中被重写实现具体的执行逻辑。
        子类必须提供此方法的具体实现，否则将无法实例化。

        Args:
            self: 类实例的引用

        Returns:
            无返回值，具体返回值类型和含义由子类实现决定
        """
        pass

    def keepAlive(self):
        """
        保持程序活跃状态

        通过模拟鼠标点击操作来防止程序被系统休眠或超时退出。
        点击屏幕右下角位置(1350, 750)来维持活跃状态。

        参数:
            self: 类实例对象

        返回值:
            无
        """
        self.click_mouse(pos=(1335, 750), post_delay=0)

    def defer(self, count=1):
        """
        延迟执行指定的秒数

        参数:
            count (int): 延迟的秒数

        返回值:
            None
        """
        # 循环等待指定的秒数
        while not self._finished.is_set() and count >= 0:
            time.sleep(1)
            count -= 1

    def logs(self, message):
        """
        发送日志消息到指定窗口

        参数:
            message: 要发送的日志消息内容

        返回值:
            无
        """
        self.queueListener.emit(
            {
                "event": "JS:EMIT",
                "args": (
                    "API:ADD:LOGS",
                    {
                        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                        "info": "信息",
                        "data": message
                    }
                )
            }
        )

    def input(self, **kwargs):
        """输入信息"""
        if self._finished.is_set():
            return False

        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            text = inner_kwargs.get('text')
            # 在停止锁的保护下执行控制台输入操作
            with self._stopped:
                self.winConsole.input(text)

        return _inner(**kwargs)

    def move_mouse(self, **kwargs):
        """鼠标从起始位置移动到结束位置"""
        if self._finished.is_set():
            return False

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            start = inner_kwargs.get('start', (0, 0))
            end = inner_kwargs.get('end', (0, 0))

            with self._stopped:
                # 执行窗口控制台的鼠标移动操作
                self.winConsole.mouse_move(start, end)

        return _inner(**kwargs)

    def click_mouse(self, **kwargs):
        """鼠标点击"""

        if self._finished.is_set():
            return False

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            pos = inner_kwargs.get('pos', (1335, 750))
            x = inner_kwargs.get('x', 0)
            y = inner_kwargs.get('y', 0)
            click_mode = inner_kwargs.get('click_mode', "random")
            press_down_delay = inner_kwargs.get('press_down_delay', 0)

            pos = [pos] if not isinstance(pos, list) else pos
            positions = [(p[0] + x, p[1] + y) for p in pos]

            # 定义各种点击模式的处理函数
            def click_first():
                self.winConsole.click_mouse(positions[0], press_down_delay=press_down_delay)

            def click_last():
                self.winConsole.click_mouse(positions[-1], press_down_delay=press_down_delay)

            def click_random():
                self.winConsole.click_mouse(random.choice(positions), press_down_delay=press_down_delay)

            def click_all():
                for p in positions:
                    self.winConsole.click_mouse(p, press_down_delay=press_down_delay)

            def click_all_reverse():
                for p in reversed(positions):
                    self.winConsole.click_mouse(p, press_down_delay=press_down_delay)

            # 模式映射字典（键：模式名称，值：对应处理函数）
            mode_handlers = {
                'first': click_first,
                'last': click_last,
                'random': click_random,
                'all': click_all,
                'all_reverse': click_all_reverse
            }

            with self._stopped:
                mode_handlers.get(click_mode, click_first)()

        return _inner(**kwargs)

    def click_key(self, **kwargs):
        """键盘点击"""

        if self._finished.is_set():
            return False

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            key = inner_kwargs.get('key', None)
            press_down_delay = inner_kwargs.get('press_down_delay', 0)

            # 执行按键操作
            with self._stopped:
                self.winConsole.click_key(key=key, press_down_delay=press_down_delay)

        return _inner(**kwargs)

    def touch(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @during(seconds=Config.OVERTIME)
        def _inner(**inner_kwargs):

            for image in args:
                results = self.template(image=image, **inner_kwargs)
                if not results:
                    continue
                self.click_mouse(pos=results, **kwargs)
                return results
            return []

        return _inner(**kwargs)

    def wait(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @during(seconds=Config.OVERTIME)
        def _inner(**inner_kwargs):

            for image in args:
                result = self.template(image=image, **inner_kwargs)
                if not result:
                    continue
                return result
            return []

        return _inner(**kwargs)

    def exits(self, *args, **kwargs):
        """在指定区域内查找图像模板，支持多次匹配和超时控制"""

        # 遍历所有待查找的图像模板
        for image in args:
            result = self.template(image=image, **kwargs)
            if not result:
                continue
            return result
        return []

    def template(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @verify()
        def _inner(**inner_kwargs):
            try:
                image = inner_kwargs.get('image', None)
                box = inner_kwargs.get('box', Config.BOX)
                find_all = inner_kwargs.get('find_all', False)
                threshold = Config.THRESHOLD_IMAGE[image] \
                    if Config.THRESHOLD_IMAGE.get(image) \
                    else inner_kwargs.get('threshold', Config.THRESHOLD)

                screen = pil_2_cv2(self.winConsole.capture.crop(box))
                template = Template(
                    f"resources/images/{self.taskConfig.model}/{image}.bmp",
                    threshold=threshold
                )
                results = template.match_all_in(screen) if find_all else template.match_in(screen)
                print(f"{image}: {results}")
                if results is None:
                    return []
                if not isinstance(results, list):
                    return [(box[0] + results[0], box[1] + results[1])]

                return sorted([
                    (box[0] + result['result'][0], box[1] + result['result'][1])
                    for result in results
                ], key=lambda pos: (-pos[0], pos[1]))

            except Exception as e:
                logging.error(e)
                return []

        return _inner(**kwargs)

