"""颜色匹配引擎 — 截屏 + RGB 像素比对"""
import logging
import numpy as np
from script.config.Setting import BOX
from script.engine.ScreenCapture import ScreenCapture


class ColorMatcher:

    @staticmethod
    def match_color(*args, **kwargs):
        """在区域内搜索匹配的像素点，返回 [(x, y), ...] 列表（绝对屏幕坐标）"""
        hwnd = kwargs.get("hwnd")
        assert hwnd is not None, "缺少窗口句柄"
        color = kwargs.get("color")
        assert color is not None, "缺少目标颜色 color=[R,G,B]"
        box = kwargs.get("box", BOX)
        tolerance = kwargs.get("tolerance", 10)

        img, _ = ScreenCapture.capture_gray(hwnd)
        h, w = img.shape[:2]
        x1, y1, x2, y2 = box
        x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))

        target = tuple(int(c) for c in color[:3])
        region = img[y1:y2, x1:x2]
        region_rgb = region[:, :, ::-1]  # BGR → RGB

        diff = np.sqrt(np.sum((region_rgb.astype(int) - np.array(target, dtype=int)) ** 2, axis=2))
        ys, xs = np.where(diff <= tolerance)

        results = [(int(x) + x1, int(y) + y1) for x, y in zip(xs, ys)]
        logging.debug(f"[ColorMatcher] color={target} tolerance={tolerance} box={box} → {len(results)} 匹配")
        return results

    @staticmethod
    def exits_color(*args, **kwargs):
        """检测区域内是否存在目标颜色，返回 True/False"""
        return bool(ColorMatcher.match_color(**kwargs))
