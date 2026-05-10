from threading import Lock
import base64

import cv2
import numpy as np
import win32con
import win32gui
import win32ui

from script.api.JsApi import js


class ScreenCapture:
    _screen_locks = {}
    _screen_locks_lock = Lock()
    _frame_counts = {}

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

            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid window dimensions: {width}x{height}")

            hwndDC = None
            mfcDC = None
            saveDC = None
            saveBitMap = None
            try:
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
            finally:
                if saveBitMap is not None:
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                if saveDC is not None:
                    saveDC.DeleteDC()
                if mfcDC is not None:
                    mfcDC.DeleteDC()
                if hwndDC is not None:
                    win32gui.ReleaseDC(hwnd, hwndDC)

            cls._push_preview(hwnd, img)

            return img, gray

    # ---- 图像预处理 ----

    @staticmethod
    def apply_preprocess(gray, config):
        """
        对灰度图做额外预处理，每个处理逻辑独立开关，可自由组合。

        config 字段（全部可选，默认 false/0）：
        ┌─────────────────────┬────────┬─────────────────────────────────┐
        │ 参数                │ 类型   │ 说明                            │
        ├─────────────────────┼────────┼─────────────────────────────────┤
        │ binarize            │ bool   │ 二值化，阈值由 binarize_threshold│
        │                     │        │ 控制。0 时用 OTSU 自动计算      │
        │ binarize_threshold  │ 0-255  │ 二值化固定阈值，0=OTSU 自动     │
        │                     │        │ 推荐范围 100-180                │
        │ binarize_invert     │ bool   │ 反转二值化结果（黑变白/白变黑） │
        │ adaptive            │ bool   │ 自适应高斯阈值（与 binarize 互斥│
        │                     │        │ 适合光照不均的场景）            │
        │ adaptive_block      │ 奇数   │ 自适应块大小，默认 11，推荐 9-15│
        │ adaptive_c          │ 2-10   │ 自适应常数，默认 2，值越大越宽松│
        └─────────────────────┴────────┴─────────────────────────────────┘

        示例：
        - 无预处理：不传 preprocess 参数
        - 仅二值化：{"binarize": true}
        - 固定阈值：{"binarize": true, "binarize_threshold": 150}
        - 二值化+反转：{"binarize": true, "binarize_invert": true}
        - 自适应：{"adaptive": true}
        - 自适应+调参：{"adaptive": true, "adaptive_block": 15, "adaptive_c": 3}

        返回处理后的灰度图。
        """
        if config is None:
            return gray

        if isinstance(config, str):
            # 旧版兼容：字符串 "binary" / "binary_inv" / "adaptive"
            config = {"type": config}

        # 旧版兼容：{"type": "binary", "value": ...}
        if "type" in config:
            ptype = config.get("type", "")
            if ptype in ("binary", "binary_inv"):
                value = config.get("value", 0)
                config = {"binarize": True, "binarize_invert": ptype == "binary_inv",
                          "binarize_threshold": value if isinstance(value, (int, float)) and value > 0 else 0}
            elif ptype == "adaptive":
                config = {"adaptive": True,
                          "adaptive_block": config.get("block", 11),
                          "adaptive_c": config.get("c", 2)}
            else:
                return gray

        result = gray

        # 自适应阈值（与二值化互斥，优先）
        if config.get("adaptive", False):
            block = int(config.get("adaptive_block", 11))
            c = int(config.get("adaptive_c", 2))
            if block % 2 == 0:
                block += 1
            result = cv2.adaptiveThreshold(result, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, block, c)

        # 二值化
        elif config.get("binarize", False):
            threshold = int(config.get("binarize_threshold", 0))
            if threshold > 0:
                _, result = cv2.threshold(result, threshold, 255, cv2.THRESH_BINARY)
            else:
                _, result = cv2.threshold(result, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 反转（可与二值化或自适应组合）
        if config.get("binarize_invert", False):
            result = cv2.bitwise_not(result)

        return result

    @classmethod
    def _push_preview(cls, hwnd, img):
        """隔帧推送缩小后的JPEG预览到前端"""
        count = cls._frame_counts.get(hwnd, 0) + 1
        cls._frame_counts[hwnd] = count
        if count % 10 != 0:
            return
        small = cv2.resize(img, (0, 0), fx=0.4, fy=0.4)
        _, buffer = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 85])
        js.update_character({
            "hwnd": hwnd,
            "preview": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        })
