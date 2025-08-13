from abc import ABC, abstractmethod

from airtest.aircv.utils import pil_2_cv2
from airtest.core.cv import Template


class BasisTask(ABC):
    def __init__(self, hwnd, stopped, finished, taskConfig, windowConsole):
        self.hwnd = hwnd
        self.stopped = stopped
        self.finished = finished
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

    def imageTemplate(self, image, threshold, box):
        if self.finished.is_set():
            return
        with self.stopped:
            screen = pil_2_cv2(self.windowConsole.captureWindow(hwnd=self.hwnd).crop(box))
            result = Template(f"resources/images/{self.taskConfig.model}/{image}.bmp", threshold=threshold).match_in(
                screen)
            print(f"{image}: {result}")
            return (box[0] + result[0], box[1] + result[1]) if result else None

    def imageTemplateAll(self, image, threshold, box):
        if self.finished.is_set():
            return
        with self.stopped:
            screen = pil_2_cv2(self.windowConsole.captureWindow(hwnd=self.hwnd).crop(box))
            results = Template(f"resources/images/{self.taskConfig.model}/{image}.bmp",
                               threshold=threshold).match_all_in(
                screen)
            print(f"{image}: {results}")
            return [
                (box[0] + result['result'][0], box[1] + result['result'][1])
                for result in results
            ]
