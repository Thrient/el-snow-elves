import time
from abc import ABC, abstractmethod
from threading import Lock, Event

from airtest.aircv.utils import pil_2_cv2
from airtest.core.cv import Template

from script.config.Config import Config
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.core.Timer import Timer
from script.functools.functools import delay, repeat


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
            if var_name in self.event:
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
        self.click_mouse(pos=(1335, 750), post_delay=1000)

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
            return None

        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            text = inner_kwargs.get('text')
            # 如果已完成标志已设置，则直接返回
            if self._finished.is_set():
                return
            # 在停止锁的保护下执行控制台输入操作
            with self._stopped:
                self.winConsole.input(text)

        return _inner(**kwargs)

    def move_mouse(self, **kwargs):
        """鼠标从起始位置移动到结束位置"""
        if self._finished.is_set():
            return None

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
            return None

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            pos = inner_kwargs.get('pos', (1335, 750))
            x = inner_kwargs.get('x', 0)
            y = inner_kwargs.get('y', 0)
            press_down_delay = inner_kwargs.get('press_down_delay', 0)

            with self._stopped:
                self.winConsole.click_mouse((pos[0] + x, pos[1] + y), press_down_delay=press_down_delay)

        return _inner(**kwargs)

    def click_key(self, **kwargs):
        """键盘点击"""

        if self._finished.is_set():
            return None

        @repeat()
        @delay(post_delay=self.taskConfig.delay)
        def _inner(**inner_kwargs):
            key = inner_kwargs.get('key', None)
            press_down_delay = inner_kwargs.get('press_down_delay', 0)

            # 执行按键操作
            with self._stopped:
                self.winConsole.click_key(key=key, press_down_delay=press_down_delay)

        return _inner(**kwargs)

    def touch_once(self, *args, **kwargs):
        """只尝试查找一次"""
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)
        for image in args:
            result = self.imageTemplate(image, threshold=threshold, box=box)
            if result is None:
                continue
            self.click_mouse(pos=result, **kwargs)
            return result
        return None

    def touch(self, *args, **kwargs):
        """查找并点击屏幕上的图像模板"""
        _start_time = time.time()

        over_time = kwargs.get('over_time', Config.OVERTIME)
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)

        while time.time() - _start_time < over_time and not self._finished.is_set():
            for image in args:
                result = self.imageTemplate(image, threshold=threshold, box=box)
                if result is None:
                    continue
                self.click_mouse(pos=result, **kwargs)
                return result
            time.sleep(0.1)
        return None

    def wait(self, *args, **kwargs):
        """
        等待指定图像出现在屏幕上，在超时时间内循环检测图像模板匹配结果

        参数:
            *args: 可变参数，传入需要等待的图像文件路径
            **kwargs: 关键字参数
                overTime: 超时时间，默认使用Config.OVERTIME配置
                threshold: 匹配阈值，默认使用Config.THRESHOLD配置
                box: 检测区域，默认使用Config.BOX配置

        返回值:
            如果在超时时间内找到匹配的图像，返回匹配结果坐标；否则返回None
        """

        __currentTIme = time.time()

        # 从kwargs中获取配置参数，如果未提供则使用默认配置
        overTime = kwargs.get('overTime', Config.OVERTIME)
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)

        # 在超时时间内循环检测图像匹配
        while time.time() - __currentTIme < overTime and not self._finished.is_set():

            # 遍历所有待检测的图像
            for image in args:
                result = self.imageTemplate(image, threshold, box)
                if result is not None:
                    return result
        return None

    def exits(self, *args, **kwargs):
        """
        在指定区域内查找图像模板，支持多次匹配和超时控制

        参数:
            *args: 可变参数，传入要查找的图像模板列表
            **kwargs: 关键字参数
                threshold: 匹配阈值，默认使用Config.THRESHOLD
                box: 查找区域，默认使用Config.BOX

        返回值:
            如果找到匹配的图像模板，返回匹配结果坐标；否则返回None
        """
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)

        # 遍历所有待查找的图像模板
        for image in args:
            result = self.imageTemplate(image, threshold, box)
            if result is not None:
                return result

        return None

    def exitsAll(self, *args, **kwargs):
        """
        在指定区域内循环查找多个图像模板，返回第一个匹配到的结果

        参数:
            *args: 可变参数，包含待查找的图像模板路径
            **kwargs: 关键字参数
                threshold: 匹配阈值，默认使用Config.THRESHOLD
                box: 查找区域，默认使用Config.BOX

        返回值:
            如果找到匹配的图像模板，返回匹配结果；否则返回None
        """
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)
        findAll = kwargs.get('findAll', False)

        results = []
        # 遍历所有待查找的图像模板
        for image in args:
            results += self.imageTemplateAll(image, threshold, box)
            if results is not None and not findAll:
                return results

        return results

    # def ocr(self, box):
    #     """ocr识别"""
    #     with self._stopped:
    #         screen = pil_2_cv2(self.windowConsole.captureWindow().crop(box))
    #         ocr = CnOcr(
    #             det_model_name="en_PP-OCRv3_det",
    #             det_model_fp="resources/cnstd/1.2/ppocr/en_PP-OCRv3_det_infer.onnx",
    #             rec_model_name="en_number_mobile_v2.0",
    #             rec_model_fp="resources/cnocr/2.3/ppocr/en_number_mobile_v2.0_rec_infer.onnx"
    #         )
    #         res = ocr.ocr_for_single_line(screen)
    #         return res

    def imageTemplate(self, image, threshold, box):
        """
        在指定窗口区域中查找模板图像的位置

        参数:
            image (str): 模板图像文件名（不包含扩展名）
            threshold (float): 图像匹配阈值，用于判断匹配程度
            box (tuple): 截图区域的坐标元组 (left, top, right, bottom)

        返回:
            tuple: 匹配成功时返回相对于原始窗口的坐标 (x, y)，匹配失败时返回 None
        """

        threshold = Config.THRESHOLD_IMAGE[image] if Config.THRESHOLD_IMAGE.get(image) else threshold

        if self._finished.is_set():
            return None
        with self._stopped:
            # 截取指定窗口的指定区域并转换为OpenCV格式
            screen = pil_2_cv2(self.winConsole.capture.crop(box))
            # 使用模板匹配算法在截图中查找指定图像
            result = Template(f"resources/images/{self.taskConfig.model}/{image}.bmp", threshold=threshold).match_in(
                screen)
            print(f"{image}: {result}")
            # 如果找到匹配结果，返回相对于原始窗口的绝对坐标
            return (box[0] + result[0], box[1] + result[1]) if result else None

    def imageTemplateAll(self, image, threshold, box):
        """
        在指定区域内查找所有匹配的图像模板位置

        参数:
            image: 要匹配的图像模板名称
            threshold: 图像匹配的阈值
            box: 截图区域的坐标框 (left, top, right, bottom)

        返回值:
            list: 匹配到的所有位置坐标列表，每个坐标为相对于原始窗口的绝对坐标
        """
        threshold = Config.THRESHOLD_IMAGE[image] if Config.THRESHOLD_IMAGE.get(image) else threshold
        if self._finished.is_set():
            return None
        with self._stopped:
            # 截取指定区域的屏幕图像并转换为OpenCV格式
            screen = pil_2_cv2(self.winConsole.capture.crop(box))
            # 在屏幕截图中查找所有匹配的模板图像
            results = Template(f"resources/images/{self.taskConfig.model}/{image}.bmp",
                               threshold=threshold).match_all_in(screen)

            print(f"{image}: {results}")
            # 将相对坐标转换为绝对坐标并返回
            return [
                (box[0] + result['result'][0], box[1] + result['result'][1])
                for result in results
            ] if results is not None else []
