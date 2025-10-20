import ctypes
import uuid
from ctypes import wintypes

import win32api
import win32gui


class Utils:

    @staticmethod
    def getHwndByTitle(title="一梦江湖"):
        results = []

        def callback(hwnd, extra):
            # 检查窗口是否可见（可选，根据需求决定是否保留）
            if win32gui.IsWindowVisible(hwnd):
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                # 检查标题是否包含目标字符串（精确匹配可改为 ==）
                if title == window_title:
                    results.append(hwnd)

        win32gui.EnumWindows(callback, None)
        return results

    @staticmethod
    def getHwndByMouseAndTitle(title="一梦江湖"):
        """
        通过鼠标当前位置获取窗口句柄

        Returns:
            int: 窗口句柄，如果获取失败则返回None
        """
        # 获取鼠标当前坐标位置
        x, y = win32api.GetCursorPos()
        # 根据坐标获取对应的窗口句柄
        hwnd = win32gui.WindowFromPoint((x, y))
        window_title = win32gui.GetWindowText(hwnd)

        if not win32gui.IsWindow(hwnd):
            return None

        if window_title != title:
            return None

        return hwnd

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
    def sendEmit(window, event, callback=None, **kwargs):
        """
        向指定窗口发送自定义事件

        :param window: 目标窗口对象，用于执行JavaScript代码
        :param callback: 回调函数
        :param event: 事件名称字符串
        :param kwargs: 传递给事件的额外参数，将作为事件数据发送
        :return: 无返回值
        """
        # 生成唯一的临时事件名（避免冲突）
        callback_event = f"__callback_{uuid.uuid4().hex}"

        # 构造事件数据（包含临时回调事件名，供前端返回结果）
        data = {**kwargs, "_callback_event": callback_event}

        js_code = f"""
            new Promise((resolve) => {{
                // 定义事件回调函数（单独提取，方便移除）
                const handleCallback = (result) => {{
                    // 1. 先移除监听（确保只执行一次）
                    window.$mitt.off('{callback_event}', handleCallback);
                    // 2. 再处理结果
                    resolve(result);
                }};
                console.log('{callback_event}')
                // 注册普通事件监听
                window.$mitt.on('{callback_event}', handleCallback);

                // 触发原事件，传递数据
                window.$mitt.emit('{event}', {data});
            }})
        """

        # 执行JavaScript代码，在window对象上触发指定事件
        return window.evaluate_js(js_code, callback=callback)

    @staticmethod
    def findWindowByTitleAndOwnerHwnd(title, ownerHwnd):
        result = None

        def callback(targetHwnd, _):
            nonlocal result
            if win32gui.GetWindow(targetHwnd, 4) == ownerHwnd and win32gui.GetWindowText(targetHwnd) == title:
                result = targetHwnd
            return True

        win32gui.EnumWindows(callback, None)
        return result
