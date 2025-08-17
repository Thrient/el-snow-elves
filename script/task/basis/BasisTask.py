import time
from abc import ABC, abstractmethod

from airtest.aircv.utils import pil_2_cv2
from airtest.core.cv import Template

from script.config.Config import Config
from script.utils.Utils import Utils


class BasisTask(ABC):
    def __init__(self, hwnd, stopped, finished, window, taskConfig, windowConsole):
        self.hwnd = hwnd
        self.stopped = stopped
        self.finished = finished
        self.window = window
        self.taskConfig = taskConfig
        self.windowConsole = windowConsole

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

    def logs(self, message):
        """
        发送日志消息到指定窗口

        参数:
            message: 要发送的日志消息内容

        返回值:
            无
        """
        Utils.sendEmit(self.window, 'API:ADD:LOGS', time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                       info="信息", data=message)

    def input(self, text):
        """
        向控制台窗口输入文本内容

        参数:
            text (str): 要输入到控制台的文本内容

        返回值:
            无返回值
        """
        # 如果已完成标志已设置，则直接返回
        if self.finished.is_set():
            return
        # 在停止锁的保护下执行控制台输入操作
        with self.stopped:
            self.windowConsole.input(text)

    def mouseClick(self, pos, x=0, y=0, timeout=Config.TIMEOUT, count=1, delay=0):
        """
        在指定位置执行鼠标点击操作

        参数:
            pos: 鼠标点击的基础位置坐标，格式为(x, y)元组
            x: 相对于基础位置的x轴偏移量, 默认0
            y: 相对于基础位置的y轴偏移量, 默认
            timeout: 每次点击后的等待时间，默认使用Config.TIMEOUT配置
            count: 点击次数，默认为1次
            delay: 鼠标按下和释放之间的时间延迟，默认为0

        返回值:
            无返回值
        """
        if self.finished.is_set():
            return
        with self.stopped:
            # 确保点击次数至少为1次
            count = 1 if count <= 0 else count
            # 执行指定次数的鼠标点击操作
            for _ in range(count):
                print(f"pos: {pos[0]}, {pos[1]}")
                self.windowConsole.mouseDownUp((pos[0] + x, pos[1] + y), delay=delay)
                time.sleep(timeout)

    def keyClick(self, key, timeout=Config.TIMEOUT, delay=0):
        """
        模拟键盘按键点击操作

        参数:
            key: 要按下的键值
            timeout: 操作后的等待时间，默认使用配置中的超时时间
            delay: 按键之间的延迟时间，默认为0

        返回值:
            无返回值
        """
        if self.finished.is_set():
            return
        # 执行按键操作
        with self.stopped:
            self.windowConsole.keyDownUp(key, delay=delay)
            print(f"key: {key}")
            time.sleep(timeout)

    def touch(self, *args, **kwargs):
        """
        在屏幕上查找并点击指定的图像模板

        参数:
            *args: 可变参数，传入要查找的图像路径列表
            **kwargs: 关键字参数
                match: 匹配次数，默认为2
                threshold: 图像匹配阈值，默认使用Config.THRESHOLD
                box: 查找区域，默认使用Config.BOX
                timeout: 超时时间，默认使用Config.TIMEOUT
                x: 点击位置的x偏移量，默认为0
                y: 点击位置的y偏移量，默认为0

        返回值:
            如果找到并点击了图像，返回匹配结果坐标；否则返回None
        """

        match = kwargs.get('match', 2)
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)
        timeout = kwargs.get('timeout', Config.TIMEOUT)
        x = kwargs.get('x', 0)
        y = kwargs.get('y', 0)

        # 循环进行多次匹配尝试
        for _ in range(match):
            # 遍历所有待查找的图像
            for image in args:
                result = self.imageTemplate(image, threshold, box)
                if result is None:
                    continue
                self.mouseClick(result, x, y)
                return result
            time.sleep(timeout)
        return None

    def exits(self, *args, **kwargs):
        """
        在指定区域内查找图像模板，支持多次匹配和超时控制

        参数:
            *args: 可变参数，传入要查找的图像模板列表
            **kwargs: 关键字参数
                match: 匹配次数，默认为1
                threshold: 匹配阈值，默认使用Config.THRESHOLD
                box: 查找区域，默认使用Config.BOX
                timeout: 超时时间，默认使用Config.TIMEOUT

        返回值:
            如果找到匹配的图像模板，返回匹配结果坐标；否则返回None
        """
        match = kwargs.get('match', 1)
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)
        timeout = kwargs.get('timeout', Config.TIMEOUT)

        # 循环进行多次匹配查找
        for _ in range(match):
            # 遍历所有待查找的图像模板
            for image in args:
                result = self.imageTemplate(image, threshold, box)
                if result is not None:
                    return result
            time.sleep(timeout)
        return None

    def exitsAll(self, *args, **kwargs):
        """
        在指定区域内循环查找多个图像模板，返回第一个匹配到的结果

        参数:
            *args: 可变参数，包含待查找的图像模板路径
            **kwargs: 关键字参数
                match: 匹配次数，默认为1次
                threshold: 匹配阈值，默认使用Config.THRESHOLD
                box: 查找区域，默认使用Config.BOX
                timeout: 超时时间，默认使用Config.TIMEOUT

        返回值:
            如果找到匹配的图像模板，返回匹配结果；否则返回None
        """
        match = kwargs.get('match', 1)
        threshold = kwargs.get('threshold', Config.THRESHOLD)
        box = kwargs.get('box', Config.BOX)
        timeout = kwargs.get('timeout', Config.TIMEOUT)

        # 循环进行多次匹配查找
        for _ in range(match):
            # 遍历所有待查找的图像模板
            for image in args:
                results = self.imageTemplateAll(image, threshold, box)
                if results is not None:
                    return results
            time.sleep(timeout)
        return None


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

        if self.finished.is_set():
            return
        with self.stopped:
            # 截取指定窗口的指定区域并转换为OpenCV格式
            screen = pil_2_cv2(self.windowConsole.captureWindow().crop(box))
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
        if self.finished.is_set():
            return
        with self.stopped:
            # 截取指定区域的屏幕图像并转换为OpenCV格式
            screen = pil_2_cv2(self.windowConsole.captureWindow().crop(box))
            # 在屏幕截图中查找所有匹配的模板图像
            results = Template(f"resources/images/{self.taskConfig.model}/{image}.bmp",
                               threshold=threshold).match_all_in(
                screen)
            print(f"{image}: {results}")
            # 将相对坐标转换为绝对坐标并返回
            return [
                (box[0] + result['result'][0], box[1] + result['result'][1])
                for result in results
            ]
