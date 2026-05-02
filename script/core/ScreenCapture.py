from threading import Lock

import cv2
import numpy as np
import win32con
import win32gui
import win32ui


class ScreenCapture:
    _screen_locks = {}
    _screen_locks_lock = Lock()

    @classmethod
    def get_screen_lock(cls, hwnd):
        with cls._screen_locks_lock:
            if hwnd not in cls._screen_locks:
                cls._screen_locks[hwnd] = Lock()
            return cls._screen_locks[hwnd]

    @classmethod
    def capture_gray(cls, hwnd):
        """捕获屏幕并返回 (彩色图, 灰度图)"""
        lock = cls.get_screen_lock(hwnd)
        with lock:
            client_rect = win32gui.GetClientRect(hwnd)
            left, top, right, bottom = client_rect
            width = right - left
            height = bottom - top

            hwndDC = win32gui.GetDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

            img = np.frombuffer(saveBitMap.GetBitmapBits(True), dtype=np.uint8).reshape((height, width, 4))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            gray = cv2.equalizeHist(gray)

            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return img, gray
