import logging
import time

import win32api
import win32con
import win32gui

from script.config.Setting import DELAY
from script.functools.Functools import delay, repeat
from script.engine.safe_sleep import safe_sleep


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
        """按下并抬起键盘按键。press > 0 时变为长按"""
        hwnd = kwargs.get("hwnd")
        predicate = kwargs.get("predicate", lambda: True)
        press = float(kwargs.get("press", 0) or 0)

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
            safe_sleep(press, lambda: not predicate())
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0xC0000001)
            label = f"长按按键: {key} 持续 {press}s" if press > 0 else f"按键: {key}"
            logging.info(f"{label} | hwnd={hwnd}")

        return _inner(**kwargs)

    @staticmethod
    def key_down(*args, **kwargs):
        """按下按键（不抬起），配合 key_up 实现长按穿插"""
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
            logging.info(f"按下按键: {key} | hwnd={hwnd}")

        return _inner(**kwargs)

    @staticmethod
    def key_up(*args, **kwargs):
        """抬起按键，配合 key_down 使用"""
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
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0xC0000001)
            logging.info(f"抬起按键: {key} | hwnd={hwnd}")

        return _inner(**kwargs)

    @staticmethod
    def mouse_click(*args, **kwargs):
        """鼠标点击。press > 0 时变为长按"""
        hwnd = kwargs.get("hwnd")
        predicate = kwargs.get("predicate", lambda: True)
        press = float(kwargs.get("press", 0) or 0)

        @repeat()
        @delay(post_delay=DELAY)
        def _inner(**inner_kwargs):
            pos = inner_kwargs.get("pos", (1335, 750))
            x = pos[0] + inner_kwargs.get("x", 0)
            y = pos[1] + inner_kwargs.get("y", 0)
            lParam = (y << 16) | x

            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            safe_sleep(press, lambda: not predicate())
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

            label = f"长按坐标: ({x}, {y}) 持续 {press}s" if press > 0 else f"点击坐标: {pos}"
            logging.info(f"{label} | hwnd={hwnd}")

        return _inner(**kwargs)

    @staticmethod
    def mouse_drag(*args, **kwargs):
        """鼠标拖拽"""
        hwnd = kwargs.get("hwnd")

        @repeat()
        @delay(post_delay=DELAY)
        def _inner(**inner_kwargs):
            start_pos = inner_kwargs.get("start_pos", (1335, 750))
            end_pos = inner_kwargs.get("end_pos", (1335 + 100, 750))
            duration = inner_kwargs.get("duration", 0.5)

            start_x = start_pos[0] + inner_kwargs.get("x", 0)
            start_y = start_pos[1] + inner_kwargs.get("y", 0)
            end_x = end_pos[0] + inner_kwargs.get("end_x", 0)
            end_y = end_pos[1] + inner_kwargs.get("end_y", 0)

            lParam = (start_y << 16) | start_x
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)

            steps = max(2, int(duration * 60))
            for i in range(1, steps + 1):
                t = i / steps
                x = int(start_x + (end_x - start_x) * t)
                y = int(start_y + (end_y - start_y) * t)
                lParam = (y << 16) | x
                win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
                time.sleep(duration / steps)

            lParam = (end_y << 16) | end_x
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

            logging.info(f"拖拽: ({start_x},{start_y}) -> ({end_x},{end_y})")

        return _inner(**kwargs)

    @staticmethod
    def input(*args, **kwargs):
        """逐字输入文本"""
        hwnd = kwargs.get("hwnd")

        @delay(post_delay=DELAY)
        def _inner(**inner_kwargs):
            text = str(inner_kwargs.get("text", ""))
            for char in text:
                win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), None)
                time.sleep(0.02)
            logging.info(f"输入文本: {text[:20]}{'...' if len(text) > 20 else ''} | hwnd={hwnd}")

        return _inner(**kwargs)
