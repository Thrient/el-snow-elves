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
    def get_rect(hwnd):
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
        """
        callback_event = f"__callback_{uuid.uuid4().hex}"
        data = {**kwargs, "_callback_event": callback_event}

        js_code = f"""
            (function() {{
                return new Promise((resolve, reject) => {{
                    // 设置超时
                    const timeoutId = setTimeout(() => {{
                        cleanup();
                    }}, 5000);

                    // 统一的清理函数
                    function cleanup() {{
                        try {{
                            if (window.$mitt && window.$mitt.off) {{
                                window.$mitt.off('{callback_event}', handleCallback);
                            }}
                        }} catch (e) {{
                            console.warn('Cleanup error:', e);
                        }}
                    }}

                    // 事件处理函数
                    function handleCallback(result) {{
                        clearTimeout(timeoutId);
                        cleanup();
                        console.log(result);
                        resolve(result);
                    }}

                    try {{
                        // 注册事件监听
                        if (window.$mitt && window.$mitt.on) {{
                            window.$mitt.on('{callback_event}', handleCallback);
                            window.$mitt.emit('{event}', {data});
                        }} else {{
                            cleanup();
                        }}
                    }} catch (error) {{
                        cleanup();
                    }}
                }});
            }})()
        """

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
