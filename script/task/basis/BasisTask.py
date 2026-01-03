import logging
import os
import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from threading import Lock, Event

from airtest.aircv.utils import pil_2_cv2
from airtest.core.cv import Template

from script.config.Config import Config
from script.config.Settings import settings
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.Timer import Timer
from script.functools.functools import delay, repeat, during, verify
from script.utils.Api import api
from script.utils.JsApi import js
from script.window.WindowInteractor import WindowInteractor

logger = logging.getLogger(__name__)


class BasisTask(ABC):
    CV_POOL = ThreadPoolExecutor(
        max_workers=max(2, min(6, os.cpu_count()))
    )

    def __init__(self, hwnd):
        super().__init__()
        self.hwnd = hwnd

        self.taskConfig = taskConfigScheduler.loadConfig(self.hwnd)
        self.windowInteractor = WindowInteractor(self.hwnd)

        self.timer = Timer()

        self._paused = Lock()
        self._finished = Event()

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
        self.logs(state)
        self._reset_state_variables(state)
        self._setup = state

    def _reset_state_variables(self, state):
        """重置变量"""
        reset_config = self.state_reset_config.get(state, {})
        for var_name, value in reset_config.items():
            if var_name not in self.event:
                continue
            self.event[var_name] = value() if callable(value) else value

    def _pause(self):
        """暂停"""
        self.timer.stop()
        self._paused.acquire()

    def _resume(self):
        """恢复"""
        try:
            self.timer.resume()
            self._paused.release()
        except Exception as e:
            logger.info(e)

    def _end(self):
        """结束"""
        self._resume()
        self._finished.set()

    def __enter__(self):
        api.on(f"API:SCRIPT:TASK:PAUSE:{self.hwnd}", self._paused)
        api.on(f"API:SCRIPT:TASK:RESUME:{self.hwnd}", self._resume)
        api.on(f"API:SCRIPT:TASK:END:{self.hwnd}", self._end)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        api.off(f"API:SCRIPT:TASK:PAUSE:{self.hwnd}", self._paused)
        api.off(f"API:SCRIPT:TASK:RESUME:{self.hwnd}", self._resume)
        api.off(f"API:SCRIPT:TASK:END:{self.hwnd}", self._end)
        self._end()

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
        self.click_mouse(pos=(1335, 750), post_delay=2)

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
        js.emit("API:LOGS:ADD", {
            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "data": message
        })

        js.emit("API:CHARACTERS:UPDATE", {
            "info": message,
            "hwnd": self.hwnd
        })

    def input(self, **kwargs):
        """输入信息"""
        if self._finished.is_set():
            return False

        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            text = inner_kwargs.get('text')
            # 在停止锁的保护下执行控制台输入操作
            with self._paused:
                self.windowInteractor.input(text)

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

            with self._paused:
                # 执行窗口控制台的鼠标移动操作
                self.windowInteractor.mouse_move(start, end)

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
                self.windowInteractor.click_mouse(positions[0], press_down_delay=press_down_delay)

            def click_last():
                self.windowInteractor.click_mouse(positions[-1], press_down_delay=press_down_delay)

            def click_random():
                self.windowInteractor.click_mouse(random.choice(positions), press_down_delay=press_down_delay)

            def click_all():
                for p in positions:
                    self.windowInteractor.click_mouse(p, press_down_delay=press_down_delay)

            def click_all_reverse():
                for p in reversed(positions):
                    self.windowInteractor.click_mouse(p, press_down_delay=press_down_delay)

            # 模式映射字典（键：模式名称，值：对应处理函数）
            mode_handlers = {
                'first': click_first,
                'last': click_last,
                'random': click_random,
                'all': click_all,
                'all_reverse': click_all_reverse
            }

            with self._paused:
                mode_handlers.get(click_mode, click_first)()

        return _inner(**kwargs)

    def click_key(self, **kwargs):
        """键盘点击"""

        if self._finished.is_set():
            return False

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            key = inner_kwargs.get('key', "")
            press_down_delay = inner_kwargs.get('press_down_delay', 0)

            # 执行按键操作
            with self._paused:
                self.windowInteractor.click_key(key=key, press_down_delay=press_down_delay)

        return _inner(**kwargs)

    def touch(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @during(seconds=Config.OVERTIME)
        def _inner(**inner_kwargs):
            results = self.template(*args, **inner_kwargs)
            if results:
                self.click_mouse(pos=results, **kwargs)
            return results

        return _inner(**kwargs)

    def wait(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @during(seconds=Config.OVERTIME)
        def _inner(**inner_kwargs):
            return self.template(*args, **inner_kwargs)

        return _inner(**kwargs)

    def exits(self, *args, **kwargs):
        """在指定区域内查找图像模板，支持多次匹配和超时控制"""

        # 遍历所有待查找的图像模板
        return self.template(*args, **kwargs)

    def exits_not(self, *args, **kwargs):
        """在指定区域内查找图像模板，支持多次匹配和超时控制"""

        # 遍历所有待查找的图像模板
        result = self.template(*args, **kwargs)
        if not result:
            return True
        return False

    def exits_color(self, *args, **kwargs):

        if self._finished.is_set():
            return False

        @verify()
        def _inner(**inner_kwargs):
            try:
                # import cv2
                x = inner_kwargs.get('x', 0)
                y = inner_kwargs.get('y', 0)
                target_color = inner_kwargs.get('target_color', (255, 255, 255))
                tolerance = inner_kwargs.get('tolerance', 10)

                coord = self.exits(*args)

                if not coord:
                    return False

                # PIL转OpenCV
                img = pil_2_cv2(self.windowInteractor.capture)
                # # 复制原图用于绘制（不修改原图）
                # img_marked = img.copy()
                #
                # # ========== 直接绘制目标像素位置（无坐标检查） ==========
                # height, width = img.shape[:2]
                # # 红色十字线（贯穿整图，醒目定位）
                # cv2.line(img_marked, (0, y), (width, y), (0, 0, 255), 2)  # 水平线（y轴）
                # cv2.line(img_marked, (x, 0), (x, height), (0, 0, 255), 2)  # 垂直线（x轴）
                # # 红色方框（目标像素周围5像素）
                # box_size = 5
                # cv2.rectangle(img_marked, (x - box_size, y - box_size), (x + box_size, y + box_size), (0, 0, 255), 2)
                # 标注像素信息（坐标+实际颜色+目标颜色）
                pixel_b, pixel_g, pixel_r = img[coord[-1][1] + y, coord[-1][0] + x]
                # text = f"X:{x} Y:{y} | 实际BGR:({pixel_b},{pixel_g},{pixel_r}) | 目标:{target_color}"
                # # 文本位置（固定在左上角，避免越界）
                # cv2.rectangle(img_marked, (10, 10), (500, 40), (0, 0, 255), -1)
                # cv2.putText(img_marked, text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                #
                # # ========== 显示标记后的图像 ==========
                # cv2.namedWindow("Target Pixel Position (ESC to close)", cv2.WINDOW_NORMAL)
                # cv2.resizeWindow("Target Pixel Position (ESC to close)", min(width, 1200), min(height, 800))
                # cv2.imshow("Target Pixel Position (ESC to close)", img_marked)
                # cv2.waitKey(0)  # 按ESC关闭窗口
                # cv2.destroyAllWindows()

                # ========== 原有颜色校验逻辑 ==========
                target_b, target_g, target_r = target_color
                max_diff = max(abs(pixel_b - target_b), abs(pixel_g - target_g), abs(pixel_r - target_r))
                return max_diff <= tolerance
            except Exception as e:
                logging.error(e)

        return _inner(**kwargs)

    def exits_not_color(self, *args, **kwargs):

        if self._finished.is_set():
            return False

        @verify()
        def _inner(**inner_kwargs):
            try:
                # import cv2
                x = inner_kwargs.get('x', 0)
                y = inner_kwargs.get('y', 0)
                target_color = inner_kwargs.get('target_color', (255, 255, 255))
                tolerance = inner_kwargs.get('tolerance', 10)

                coord = self.exits(*args)

                if not coord:
                    return True

                # PIL转OpenCV
                img = pil_2_cv2(self.windowInteractor.capture)
                # # 复制原图用于绘制（不修改原图）
                # img_marked = img.copy()
                #
                # # ========== 直接绘制目标像素位置（无坐标检查） ==========
                # height, width = img.shape[:2]
                # # 红色十字线（贯穿整图，醒目定位）
                # cv2.line(img_marked, (0, y), (width, y), (0, 0, 255), 2)  # 水平线（y轴）
                # cv2.line(img_marked, (x, 0), (x, height), (0, 0, 255), 2)  # 垂直线（x轴）
                # # 红色方框（目标像素周围5像素）
                # box_size = 5
                # cv2.rectangle(img_marked, (x - box_size, y - box_size), (x + box_size, y + box_size), (0, 0, 255), 2)
                # 标注像素信息（坐标+实际颜色+目标颜色）
                pixel_b, pixel_g, pixel_r = img[coord[-1][1] + y, coord[-1][0] + x]
                # text = f"X:{x} Y:{y} | 实际BGR:({pixel_b},{pixel_g},{pixel_r}) | 目标:{target_color}"
                # # 文本位置（固定在左上角，避免越界）
                # cv2.rectangle(img_marked, (10, 10), (500, 40), (0, 0, 255), -1)
                # cv2.putText(img_marked, text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                #
                # # ========== 显示标记后的图像 ==========
                # cv2.namedWindow("Target Pixel Position (ESC to close)", cv2.WINDOW_NORMAL)
                # cv2.resizeWindow("Target Pixel Position (ESC to close)", min(width, 1200), min(height, 800))
                # cv2.imshow("Target Pixel Position (ESC to close)", img_marked)
                # cv2.waitKey(0)  # 按ESC关闭窗口
                # cv2.destroyAllWindows()

                # ========== 原有颜色校验逻辑 ==========
                target_b, target_g, target_r = target_color
                max_diff = max(abs(pixel_b - target_b), abs(pixel_g - target_g), abs(pixel_r - target_r))
                return max_diff > tolerance
            except Exception as e:
                logging.error(e)

        return _inner(**kwargs)

    def template(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        if self._finished.is_set():
            return []

        @verify()
        def _inner(*inner_args, **inner_kwargs):
            try:
                with self._paused:
                    box = inner_kwargs.get('box', Config.BOX)
                    find_all = inner_kwargs.get('find_all', False)
                    screen = pil_2_cv2(self.windowInteractor.capture.crop(box))




                    futures = [
                        self.CV_POOL.submit(
                            self.cv_match_worker,
                            screen,
                            find_all,
                            f"resources/images/{self.taskConfig.model}/{img}.bmp",
                            threshold= inner_kwargs.get('threshold') if inner_kwargs.get('threshold') is not None else settings.THRESHOLD_IMAGE.get(img, settings.THRESHOLD)
                        )
                        for img in inner_args
                    ]

                    results = []

                    for future in as_completed(futures):
                        result = future.result()
                        if result is None:
                            continue
                        results += result

                    logging.info( f"{inner_args}:{results}")
                    return sorted([
                        (box[0] + result['result'][0], box[1] + result['result'][1])
                        for result in results
                    ], key=lambda pos: (-pos[0], pos[1]))

            except Exception as e:
                logging.error(e)


        return _inner(*args, **kwargs)

    @staticmethod
    @lru_cache(maxsize=512)
    def _get_template(path, threshold):
        return Template(path, threshold=threshold)

    def cv_match_worker(self, screen, find_all, path, threshold):
        # return self._get_template(path, threshold).match_all_in(screen)
        if find_all:
            return self._get_template(path, threshold).match_all_in(screen)
        result = self._get_template(path, threshold).match_in(screen)
        if result:
            return [{"result": result}]
        return []


