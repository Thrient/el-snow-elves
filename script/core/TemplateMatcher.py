import atexit
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from airtest.core.cv import Template

from script.config.Setting import BOX, THRESHOLD, PROJECT_ROOT
from script.core.ScreenCapture import ScreenCapture
from script.util.Utils import Utils

logging.getLogger("airtest").setLevel(logging.WARNING)


class TemplateMatcher:
    _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="Matcher")

    @staticmethod
    def get_template_path(category, image):
        path = os.path.join(PROJECT_ROOT, "resources", "config", category, "images", f"{image}.bmp")
        if os.path.exists(path):
            return path
        return os.path.join(PROJECT_ROOT, "resources", "images", f"{image}.bmp")

    @staticmethod
    @lru_cache(maxsize=512)
    def load_template(category, image, threshold):
        path = TemplateMatcher.get_template_path(category, image)
        return Template(path, threshold=threshold)

    def match_single(self, img, image, category, box, threshold=THRESHOLD):
        """匹配单个模板"""
        x1, y1, x2, y2 = box
        img = img[y1:y2, x1:x2]
        result = self.load_template(category=category, image=image, threshold=threshold).match_in(img)
        return [] if result is None else [(result[0] + x1, result[1] + y1)]

    def batch_match(self, *args, **kwargs):
        """批量模板匹配，一次截图匹配多个模板"""
        hwnd = kwargs.get("hwnd")
        assert hwnd is not None, "缺少窗口句柄"

        box = kwargs.get("box", BOX)
        threshold = kwargs.get("threshold", THRESHOLD)
        name = kwargs.get("name", "default")
        version = kwargs.get("version", "1.0.0")

        img, gray = ScreenCapture.capture_gray(hwnd=hwnd)

        results = []
        futures = {}

        for image in args:
            futures[self._executor.submit(
                self.match_single,
                img=img,
                image=image,
                category=fr"{name}/{version}",
                box=box,
                threshold=threshold,
            )] = image

        for future in as_completed(futures):
            try:
                result = future.result()
                results.extend(result)
            except Exception as e:
                logging.error(f"模板匹配失败: {futures[future]} | {e}")

        results = sorted(Utils.clean_duplicate_points(results), key=lambda pos: (-pos[1], pos[0]))
        logging.info(f"模板匹配完成，共 {len(results)} 个结果: {args}")
        return results


atexit.register(TemplateMatcher._executor.shutdown)
