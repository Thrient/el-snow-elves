import logging

import win32api
import win32con
import win32gui

from script.config.Setting import DELAY
from script.functools.Functools import delay, repeat


class InputSimulator:
    VK_CODE = {
        "ENTER": 0x0D, "ESCAPE": 0x1B, "SPACE": 0x20, "TAB": 0x09,
        "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
        "LEFT": 0x25, "RIGHT": 0x27, "UP": 0x26, "DOWN": 0x28,
        "DIGIT0": 0x30, "DIGIT1": 0x31, "DIGIT2": 0x32, "DIGIT3": 0x33,
        "DIGIT4": 0x34, "DIGIT5": 0x35, "DIGIT6": 0x36, "DIGIT7": 0x37,
        "DIGIT8": 0x38, "DIGIT9": 0x39,
        "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62, "NUMPAD3": 0x63,
        "NUMPAD4": 0x64, "NUMPAD5": 0x65, "NUMPAD6": 0x66, "NUMPAD7": 0x67,
        "NUMPAD8": 0x68, "NUMPAD9": 0x69,
        "ESC": 0x1B,
    }

    @staticmethod
    def key_click(*args, **kwargs):
        """按下并抬起键盘按键"""
        hwnd = kwargs.get("hwnd")

        @repeat()
        @delay(post_delay=DELAY)
        def _inner(**inner_kwargs):
            key = inner_kwargs.get("key", "")
            if isinstance(key, str):
                key_upper = key.upper()
                if key_upper in InputSimulator.VK_CODE:
                    vk_code = InputSimulator.VK_CODE[key_upper]
                else:
                    vk_code = ord(key_upper)
            else:
                vk_code = key
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, (scan_code << 16) | 1)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0xC0000001)
            logging.debug(f"按键: {key} | hwnd={hwnd}")

        return _inner(**kwargs)

    @staticmethod
    def mouse_click(*args, **kwargs):
        """鼠标点击"""
        hwnd = kwargs.get("hwnd")

        @repeat()
        @delay(post_delay=DELAY)
        def _inner(**inner_kwargs):
            pos = inner_kwargs.get("pos", (1335, 750))
            x = pos[0] + inner_kwargs.get("x", 0)
            y = pos[1] + inner_kwargs.get("y", 0)
            lParam = (y << 16) | x

            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

            logging.debug(f"点击坐标: {pos}")

        return _inner(**kwargs)
