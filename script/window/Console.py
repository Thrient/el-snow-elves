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


