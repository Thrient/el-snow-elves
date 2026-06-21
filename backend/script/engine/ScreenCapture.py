# pyright: reportUnresolvedReference=false
import base64
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
                gray = ScreenCapture.baseline_preprocess(gray)
            finally:
                if saveBitMap is not None:
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                if saveDC is not None:
                    saveDC.DeleteDC()
                if mfcDC is not None:
                    mfcDC.DeleteDC()
                if hwndDC is not None:
                    win32gui.ReleaseDC(hwnd, hwndDC)

            return img, gray

    @staticmethod
    def baseline_preprocess(gray):
        """capture_gray 对灰度图做的基准预处理（GaussianBlur + equalizeHist）。
        外部调用方可用此方法对齐预处理步骤。"""
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.equalizeHist(gray)

    @classmethod
    def capture_base64(cls, hwnd, fmt: str = "jpg"):
        """截图并返回 base64 data URL dict。fmt: 'jpg' | 'png'"""
        img, _ = cls.capture_gray(hwnd)
        ext = "." + fmt
        params = [cv2.IMWRITE_PNG_COMPRESSION, 3] if fmt == "png" else [cv2.IMWRITE_JPEG_QUALITY, 90]
        _, buffer = cv2.imencode(ext, img, params)
        return {
            "base64": f"data:image/{fmt};base64,{base64.b64encode(buffer).decode('utf-8')}",
            "width": img.shape[1],
            "height": img.shape[0],
        }

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

        # 自动转换 BGR → 灰度
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

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

        # CLAHE（对比度受限自适应直方图均衡）
        if config.get("clahe", False):
            clip = float(config.get("clahe_clip", 2.0))
            clahe_obj = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
            result = clahe_obj.apply(result)

        # Canny 边缘检测
        if config.get("canny", False):
            low = int(config.get("canny_low", 50))
            high = int(config.get("canny_high", 150))
            result = cv2.Canny(result, low, high)

        # 膨胀 / 腐蚀
        morph = None
        if config.get("dilate", False):
            morph = "dilate"
        elif config.get("erode", False):
            morph = "erode"
        if morph:
            ksize = int(config.get("morph_size", 3))
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
            result = cv2.dilate(result, kernel) if morph == "dilate" else cv2.erode(result, kernel)

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
