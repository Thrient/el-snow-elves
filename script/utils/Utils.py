import ctypes
from ctypes import wintypes

import win32api
import win32gui


class Utils:

    @staticmethod
    def getHwndByMouse():
        """
        通过鼠标当前位置获取窗口句柄

        Returns:
            int: 窗口句柄，如果获取失败则返回None
        """
        # 获取鼠标当前坐标位置
        x, y = win32api.GetCursorPos()
        # 根据坐标获取对应的窗口句柄
        hwnd = win32gui.WindowFromPoint((x, y))
        # 验证窗口句柄的有效性
        if hwnd and win32gui.IsWindow(hwnd):
            return hwnd
        return None

    @staticmethod
    def getOptimalBitmapMode(bits_pixel):
        """根据颜色深度确定PIL的原始解码模式"""
        if bits_pixel == 32:
            return 'BGRX'
        elif bits_pixel == 24:
            return 'BGR'
        elif bits_pixel == 16:
            return 'BGR;16'
        else:
            raise ValueError(f"Unsupported color depth: {bits_pixel} bits per pixel")

    @staticmethod
    def getWinRect(hwnd):
        """
        获取窗口的精确边界矩形坐标

        参数:
            hwnd: 窗口句柄，用于标识要获取边界的窗口

        返回值:
            tuple: 包含四个整数值的元组(left, top, right, bottom)，表示窗口的左、上、右、下边界坐标

        说明:
            该函数通过调用Windows DWM(Desktop Window Manager) API来获取窗口的实际显示边界，
            包括窗口的阴影和边框等视觉效果所占用的空间
        """
        # 调用DWM API获取窗口属性
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
        rect = wintypes.RECT()
        f(wintypes.HWND(hwnd),
          wintypes.DWORD(9),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return rect.left, rect.top, rect.right, rect.bottom

    @staticmethod
    def sendEmit(window, event, **kwargs):
        """
        向指定窗口发送自定义事件

        :param window: 目标窗口对象，用于执行JavaScript代码
        :param event: 事件名称字符串
        :param kwargs: 传递给事件的额外参数，将作为事件数据发送
        :return: 无返回值
        """
        # 构造事件数据对象
        data = {**kwargs}
        # 执行JavaScript代码，在window对象上触发指定事件
        return window.evaluate_js(f"window.$mitt.emit('{event}', {data})")
