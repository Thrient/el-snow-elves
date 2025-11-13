import ctypes
import math
import time
from ctypes import wintypes

import win32api
import win32con
import win32gui
import win32ui
from PIL import Image

from script.utils.Utils import Utils


class Console:
    """窗口控制"""

    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.rect = None
        self.style = None
        self.vk_code = {
            "TAB": 0x09,
            "ESC": 0x1B,
            "SPACE": 0x20,
            "DIGIT0": 0x30,
            "DIGIT1": 0x31,
            "DIGIT2": 0x32,
            "DIGIT3": 0x33,
            "DIGIT4": 0x34,
            "DIGIT5": 0x35,
            "DIGIT6": 0x36,
            "DIGIT7": 0x37,
            "DIGIT8": 0x38,
            "DIGIT9": 0x39,
            "NUMPAD0": 0x60,
            "NUMPAD1": 0x61,
            "NUMPAD2": 0x62,
            "NUMPAD3": 0x63,
            "NUMPAD4": 0x64,
            "NUMPAD5": 0x65,
            "NUMPAD6": 0x66,
            "NUMPAD7": 0x67,
            "NUMPAD8": 0x68,
            "NUMPAD9": 0x69,
        }
        self.init()

    def init(self):
        """初始化参数"""
        # 保存窗口默认值
        self.rect = win32gui.GetWindowRect(self.hwnd)
        # 储存窗口默认样式
        self.style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)

    def click_mouse(self, pos, press_down_delay):
        """鼠标左键单击"""
        x, y = pos
        position = win32api.MAKELONG(x, y)
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
        time.sleep(press_down_delay)
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, position)

    def mouse_move(self, start, end, duration=None):
        """模拟鼠标拖拽操作

        Args:
            start: 起始坐标 (x, y)
            end: 结束坐标 (x, y)
            duration: 拖拽总时长(秒)，为None时根据距离自动计算
        """
        start_x, start_y = start
        end_x, end_y = end

        # 计算移动距离
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # 自动计算持续时间（如果未指定）
        duration = max(0.1, min(1.0, distance * 0.005)) if duration is None else duration

        # 计算步数（基于时间和距离）
        min_steps = max(5, int(distance * 0.05))  # 最少5步或距离的10%
        max_steps = 60  # 最大步数限制
        steps = min(max_steps, max(min_steps, int(duration * 30)))

        try:
            # 按下左键
            start_position = win32api.MAKELONG(start_x, start_y)
            win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, start_position)

            # 平滑移动
            start_time = time.time()

            for step in range(steps + 1):
                # 使用缓动函数实现平滑移动
                progress = step / steps
                # 使用三次缓动函数，更自然的移动效果
                t = progress ** 2

                current_x = int(start_x + dx * t)
                current_y = int(start_y + dy * t)

                # 发送鼠标移动消息
                current_position = win32api.MAKELONG(current_x, current_y)
                win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, current_position)

                # 精确控制时间间隔
                elapsed = time.time() - start_time
                expected_time = step * duration / steps
                time.sleep(max(0.0, expected_time - elapsed))

        except Exception as e:
            raise e
        finally:
            # 释放左键
            win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(end_x, end_y))

    def mouse_wheel(self, pos, delta):
        """鼠标滚轮滚动"""
        x, y = pos
        position = win32api.MAKELONG(x, y)

        wparam = (delta & 0xFFFF) << 16

        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEWHEEL, wparam, position)

    def get_rect(self):
        # noinspection PyUnresolvedReferences
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
        rect = wintypes.RECT()
        f(wintypes.HWND(self.hwnd),
          wintypes.DWORD(9),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return rect.left, rect.top, rect.right, rect.bottom

    def get_vk_code(self, key):
        """获取虚拟按键码"""
        if len(key) == 1:
            # noinspection PyUnresolvedReferences
            return ctypes.windll.user32.VkKeyScanA(ord(key)) & 0xFF
        # 如果key是字符串，则从vkCode字典中获取对应的虚拟键码
        else:
            return self.vk_code[key]

    def click_key(self, key, press_down_delay):
        """键盘点击"""
        if key is None:
            return
        wparam = self.get_vk_code(key)
        # noinspection PyUnresolvedReferences
        lparam = (ctypes.windll.user32.MapVirtualKeyW(wparam, 0) << 16) | 1
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, wparam, lparam)
        time.sleep(press_down_delay)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, wparam, lparam)

    def set_style_no_menu(self):
        """设置窗口无菜单"""
        # 设置进程DPI感知级别
        # noinspection PyUnresolvedReferences
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

        # 扩展窗口新样式
        style = self.style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU)

        # 应用窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)

        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            self.rect[0],
            self.rect[1],
            1335,
            750,
            win32con.SWP_FRAMECHANGED,
        )

    def rest_style(self):
        """重置窗口样式"""
        # 设置窗口原始样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, self.style)
        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            self.rect[0],
            self.rect[1],
            1335,
            750,
            win32con.SWP_FRAMECHANGED
        )

    def enable_click_through(self):
        """激活窗口点击穿透"""

        # 获取当前窗口样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        # 添加分层和透明扩展样式标志
        style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        # 应用窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
        )

    def disable_click_through(self):
        """取消窗口点击穿透"""

        # 获取当前窗口样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # 移除分层和透明扩展样式
        style &= ~(win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

        # 应用窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)

        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
        )

    def set_transparent(self, transparent):
        """设置透明度"""

        # 获取当前窗口的扩展样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # 添加WS_EX_LAYERED样式
        style |= win32con.WS_EX_LAYERED

        # 修改窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)

        # 设置窗口透明度（LWA_ALPHA表示使用alpha值控制透明度）
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, transparent, win32con.LWA_ALPHA)

        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
        )

    def full_screen(self):
        """全屏窗口"""

        # 设置系统级别DPI感知
        # noinspection PyUnresolvedReferences
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

        # 获取窗口左上角所在屏幕的设备上下文
        screen_dc = win32api.MonitorFromWindow(self.hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        # 屏幕完整矩形（x1,y1,x2,y2）
        monitor_info = win32api.GetMonitorInfo(screen_dc)
        screen_rect = monitor_info["Monitor"]
        screen_width = screen_rect[2] - screen_rect[0]
        screen_height = screen_rect[3] - screen_rect[1]

        # 获取当前窗口样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        style &= ~(
                win32con.WS_CAPTION |  # 移除标题栏
                win32con.WS_THICKFRAME |  # 移除可调整大小边框
                win32con.WS_MINIMIZE |  # 禁用最小化
                win32con.WS_MAXIMIZEBOX |  # 移除最大化按钮
                win32con.WS_SYSMENU  # 移除系统菜单（右键菜单）
        )

        # 应用窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)

        # 重绘窗口
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,
            screen_rect[0],
            screen_rect[1],
            screen_width,
            screen_height,
            win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
        )

    def input(self, text):
        """输入消息"""
        wideText = str(text).encode('utf-16-le')

        # 逐个处理每个宽字符
        for i in range(0, len(wideText), 2):
            # 从字节中解析出宽字符值
            char_code = (wideText[i + 1] << 8) | wideText[i]

            # 发送WM_CHAR消息 (WM_CHAR的值为0x0102)
            # noinspection PyUnresolvedReferences
            ctypes.windll.user32.PostMessageW(self.hwnd, 0x0102, char_code, 0)

            # 模拟键入延迟
            time.sleep(0.05)

    @property
    def capture(self):
        """捕获窗口"""

        try:
            rect = self.get_rect()

            if rect[2] - rect[0] <= 0 or rect[3] - rect[1] <= 0:
                raise ValueError(f"Invalid window dimensions: {rect}")

            left, top, right, bottom = rect
            width, height = right - left, bottom - top

            with Console.GdiContext(self.hwnd) as (hwnd_dc, mfc_dc, save_dc, bitmap):
                # 执行位块传输捕获内容
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

                # 获取位图元数据
                bmp_info = bitmap.GetInfo()
                bits = bitmap.GetBitmapBits(True)

                # 计算对齐后的行跨距
                bits_pixel = bmp_info['bmBitsPixel']
                stride = ((width * bits_pixel + 31) // 32) * 4

                # 转换到PIL图像
                return Image.frombuffer(
                    'RGB',
                    (width, height),
                    bits,
                    'raw',
                    Utils.getOptimalBitmapMode(bits_pixel),
                    stride,
                    1
                )
        except Exception as e:
            raise RuntimeError(f"Screenshot failed: {str(e)}") from e

    class GdiContext:
        """安全管理GDI资源的上下文管理器"""

        def __init__(self, hwnd):
            self.hwnd = hwnd
            self.hwnd_dc = None
            self.mfc_dc = None
            self.save_dc = None
            self.bitmap = None

        def __enter__(self):
            """
            上下文管理器的进入方法，用于初始化窗口截图所需的设备上下文和位图资源。

            该方法会获取目标窗口的设备上下文，创建兼容的内存设备上下文和位图，
            为后续的窗口截图操作准备必要的资源。

            Returns:
                tuple: 包含(hwnd_dc, mfc_dc, save_dc, bitmap)的元组
                    - hwnd_dc: 窗口设备上下文句柄
                    - mfc_dc: 从窗口DC创建的MFC设备上下文对象
                    - save_dc: 兼容的内存设备上下文对象
                    - bitmap: 兼容位图对象

            Raises:
                RuntimeError: 当无法获取窗口设备上下文时抛出异常
            """
            # 获取窗口设备上下文
            self.hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            if not self.hwnd_dc:
                raise RuntimeError("Cannot acquire window DC")

            # 创建兼容设备上下文
            self.mfc_dc = win32ui.CreateDCFromHandle(self.hwnd_dc)
            self.save_dc = self.mfc_dc.CreateCompatibleDC()

            # 创建兼容位图
            rect = Console(self.hwnd).get_rect()
            width, height = rect[2] - rect[0], rect[3] - rect[1]
            self.bitmap = win32ui.CreateBitmap()
            self.bitmap.CreateCompatibleBitmap(self.mfc_dc, width, height)
            self.save_dc.SelectObject(self.bitmap)

            return self.hwnd_dc, self.mfc_dc, self.save_dc, self.bitmap

        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            上下文管理器退出方法，用于清理和释放Windows图形设备上下文资源

            参数:
                exc_type: 异常类型，如果没有异常则为None
                exc_val: 异常值，如果没有异常则为None
                exc_tb: 异常追踪信息，如果没有异常则为None

            返回值:
                None
            """
            # 逆序清理资源
            if self.bitmap:
                win32gui.DeleteObject(self.bitmap.GetHandle())
            if self.save_dc:
                self.save_dc.DeleteDC()
            if self.mfc_dc:
                self.mfc_dc.DeleteDC()
            if self.hwnd_dc:
                win32gui.ReleaseDC(self.hwnd, self.hwnd_dc)
