import ctypes
import math
import time
from ctypes import wintypes
from typing import Optional, Tuple

import win32api
import win32con
import win32gui
import win32ui
from PIL import Image

from script.utils.Utils import Utils


class Console:
    """窗口控制"""

    # 常用虚拟键码缓存（避免重复定义）
    VK_CODE = {
        "TAB": 0x09, "ESCAPE": 0x1B, "SPACE": 0x20,
        "DIGIT0": 0x30, "DIGIT1": 0x31, "DIGIT2": 0x32, "DIGIT3": 0x33,
        "DIGIT4": 0x34, "DIGIT5": 0x35, "DIGIT6": 0x36, "DIGIT7": 0x37,
        "DIGIT8": 0x38, "DIGIT9": 0x39,
        "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62, "NUMPAD3": 0x63,
        "NUMPAD4": 0x64, "NUMPAD5": 0x65, "NUMPAD6": 0x66, "NUMPAD7": 0x67,
        "NUMPAD8": 0x68, "NUMPAD9": 0x69,
    }

    def __init__(self, hwnd):
        self.hwnd = hwnd
        self._original_style: Optional[int] = None
        self._original_exstyle: Optional[int] = None
        self._original_rect: Optional[Tuple[int, int, int, int]] = None

        self._init_window_state()

    def _init_window_state(self):
        # noinspection PyUnresolvedReferences
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        """初始化时保存窗口原始状态（用于恢复）"""
        self._original_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        self._original_exstyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        self._original_rect = win32gui.GetWindowRect(self.hwnd)

    # ====================== 鼠标操作 ======================
    def click_mouse(self, pos: Tuple[int, int], press_down_delay: float = 0.05):
        """精准左键单击"""
        x, y = pos
        lparam = win32api.MAKELONG(x, y)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        if press_down_delay > 0:
            time.sleep(press_down_delay)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)

    def mouse_move(self, start: Tuple[int, int], end: Tuple[int, int], duration: float = None):
        """平滑拖拽（三次缓动，更自然）"""
        sx, sy = start
        ex, ey = end
        dx, dy = ex - sx, ey - sy
        distance = math.hypot(dx, dy)

        duration = duration or max(0.15, min(0.8, distance * 0.004))
        steps = min(60, max(8, int(duration * 60)))  # 60fps 左右

        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, win32api.MAKELONG(sx, sy))

        start_time = time.perf_counter()
        for i in range(1, steps + 1):
            progress = i / steps
            t = progress * progress * progress  # cubic ease-out
            x = int(sx + dx * t)
            y = int(sy + dy * t)
            win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))

            expected = i * duration / steps
            elapsed = time.perf_counter() - start_time
            if expected > elapsed:
                time.sleep(expected - elapsed)

        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(ex, ey))

    # ====================== 键盘操作 ======================
    def get_vk_code(self, key: str) -> int:
        if len(key) == 1 and key.isascii():
            return ctypes.windll.user32.VkKeyScanA(ord(key)) & 0xFF
        return self.VK_CODE.get(key.upper(), 0)

    def click_key(self, key: str, press_down_delay: float = 0.05):
        vk = self.get_vk_code(key)
        if vk == 0:
            return
        scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        lparam_down = (scan << 16) | 1
        lparam_up = (scan << 16) | 0xC0000001

        win32api.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk, lparam_down)
        time.sleep(press_down_delay)
        win32api.SendMessage(self.hwnd, win32con.WM_KEYUP, vk, lparam_up)

    def input(self, text: str, delay: float = 0.05):
        """输入文本（支持中文）"""
        wideText = str(text).encode('utf-16-le')

        # 逐个处理每个宽字符
        for i in range(0, len(wideText), 2):
            # 从字节中解析出宽字符值
            char_code = (wideText[i + 1] << 8) | wideText[i]

            # 发送WM_CHAR消息 (WM_CHAR的值为0x0102)
            # noinspection PyUnresolvedReferences
            win32api.SendMessage(self.hwnd, win32con.WM_CHAR, char_code, 0)

            # 模拟键入延迟
            time.sleep(delay)

    # ====================== 窗口样式控制 ======================
    def borderless(self):
        """无边框窗口（保留任务栏图标）"""
        style = self._original_style & ~(
                win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU
        )
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)
        win32gui.SetWindowPos(
            self.hwnd,
            0,
            self._original_rect[0],
            self._original_rect[1],
            1335,
            750,
            win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
        )

    def restore_style(self):
        """恢复原始窗口样式"""
        if self._original_style is not None:
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, self._original_style)
            win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

    def enable_click_through(self):
        exstyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        exstyle |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exstyle)
        win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

    def disable_click_through(self):
        exstyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        exstyle &= ~(win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exstyle)
        win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

    def set_transparent(self, alpha: int = 255):
        exstyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        exstyle |= win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exstyle)
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, alpha, win32con.LWA_ALPHA)

    def full_screen(self):
        monitor = win32api.MonitorFromWindow(self.hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        monitor_info = win32api.GetMonitorInfo(monitor)
        left, top, right, bottom = monitor_info["Monitor"]

        style = self._original_style & ~(
                win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU
        )
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)

        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_NOTOPMOST,
            left,
            top,
            right - left,
            bottom - top,
            win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
        )

    def get_rect(self) -> Tuple[int, int, int, int]:
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
        rect = wintypes.RECT()
        f(wintypes.HWND(self.hwnd),
          wintypes.DWORD(9),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return rect.left, rect.top, rect.right, rect.bottom

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
