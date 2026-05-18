# pyright: reportUnresolvedReference=false, reportUnresolvedImport=false
# type: ignore
import atexit
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np


def _imread_unicode(path: str):
    """cv2.imread 不支持中文路径，通过 numpy 绕开"""
    with open(path, "rb") as f:
        data = f.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)
from airtest.aircv.template_matching import TemplateMatching

from script.config.Setting import BOX, THRESHOLD, PROJECT_ROOT, PREPROCESS_KEYS
from script.core.ScreenCapture import ScreenCapture
from script.util.Utils import Utils

logging.getLogger("airtest").setLevel(logging.WARNING)


class TemplateMatcher:
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="Matcher")

    _MATCH_COLORS = [
        (0.95, (0, 255, 0)),
        (0.9,  (0, 200, 255)),
        (0.0,  (0, 140, 255)),
    ]

    @staticmethod
    def get_template_path(category, image):
        path = os.path.join(PROJECT_ROOT, "resources", "config", category, "images", f"{image}.bmp")
        return path if os.path.exists(path) else os.path.join(PROJECT_ROOT, "resources", "images", f"{image}.bmp")

    @staticmethod
    def match_single(img, image, category, box, threshold=THRESHOLD, preprocess=None):
        """匹配单个模板文件（核心匹配入口）"""
        x1, y1, x2, y2 = box
        search = ScreenCapture.apply_preprocess(img[y1:y2, x1:x2], preprocess)
        tpl_img = ScreenCapture.apply_preprocess(_imread_unicode(TemplateMatcher.get_template_path(category, image)), preprocess)
        results = TemplateMatcher._match(search, tpl_img, threshold)
        if not results:
            return []
        best = results[0]
        rect = best["rectangle"]
        # airtest rectangle 格式: (x, y, w, h) 扁平 4 元组
        if len(rect) == 4:
            px, py, w, h = rect
        else:
            (px, py), (w, h) = rect
        return [(px + w // 2 + x1, py + h // 2 + y1)]

    @staticmethod
    def _match(search_img, template_img, threshold):
        """核心匹配算法：所有匹配最终汇集于此。"""
        # airtest 内部 img_mat_rgb_2_gray 要求 3 通道输入（numpy 2.x 兼容）
        if search_img.ndim == 2:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_GRAY2BGR)
        if template_img.ndim == 2:
            template_img = cv2.cvtColor(template_img, cv2.COLOR_GRAY2BGR)
        return TemplateMatching(template_img, search_img, threshold=threshold, rgb=False).find_all_results()

    @staticmethod
    def batch_match(*args, **kwargs):
        """批量模板匹配，一次截图匹配多个模板"""
        hwnd = kwargs.get("hwnd")
        assert hwnd is not None, "缺少窗口句柄"

        box = kwargs.get("box", BOX)
        threshold = kwargs.get("threshold", THRESHOLD)
        preprocess = kwargs.get("preprocess", None)
        name = kwargs.get("name", "default")
        version = kwargs.get("version", "1.0.0")

        img, _ = ScreenCapture.capture_gray(hwnd=hwnd)

        results = []
        futures = {}
        for image in args:
            futures[TemplateMatcher.executor.submit(
                TemplateMatcher.match_single,
                img=img, image=image, category=os.path.join(name, version),
                box=box, threshold=threshold, preprocess=preprocess,
            )] = image

        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                logging.error(f"模板匹配失败: {futures[future]} | {e}")

        results = sorted(Utils.clean_duplicate_points(results), key=lambda pos: (-pos[1], pos[0]))
        logging.debug(f"模板匹配完成，共 {len(results)} 个结果: {args}")
        return results

    # ── 裁剪匹配 ──

    @staticmethod
    def match_crop(search_img: np.ndarray, crop: dict, original: np.ndarray,
                   preprocess_cfg: dict | None, threshold: float) -> list[dict]:
        """对裁剪区域运行模板匹配。返回 [{"x","y","w","h","confidence"}, ...]"""
        x, y = int(crop["x"]), int(crop["y"])
        w, h = int(crop["w"]), int(crop["h"])
        ih, iw = original.shape
        if not (w > 4 and h > 4 and 0 <= x and x + w <= iw and 0 <= y and y + h <= ih):
            logging.warning(f"[Matcher] 无效的 crop: {crop}")
            return []

        template = ScreenCapture.apply_preprocess(original[y:y+h, x:x+w], preprocess_cfg)
        processed = ScreenCapture.apply_preprocess(search_img, preprocess_cfg)
        logging.info(f"[Matcher] 模板: {template.shape[1]}x{template.shape[0]}, 搜索: {processed.shape[1]}x{processed.shape[0]}")

        results = TemplateMatcher._match(processed, template, threshold)
        return [{"x": int(r["rectangle"][0][0]), "y": int(r["rectangle"][0][1]),
                 "w": w, "h": h, "confidence": round(r["confidence"], 4)} for r in (results or [])]

    # ── 可视化 ──

    @staticmethod
    def visualize(search_img: np.ndarray, matches: list[dict]) -> str:
        """标注匹配框，返回 base64 JPEG。"""
        annotated = cv2.cvtColor(search_img, cv2.COLOR_GRAY2BGR)
        for m in matches:
            px, py, pw, ph = m["x"], m["y"], m["w"], m["h"]
            conf = m["confidence"]
            color = TemplateMatcher._MATCH_COLORS[-1][1]
            for thresh, c in TemplateMatcher._MATCH_COLORS:
                if conf >= thresh:
                    color = c
                    break
            cv2.rectangle(annotated, (px, py), (px + pw, py + ph), color, 2)
            label = f"{conf:.3f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (px, py - th - 4), (px + tw + 4, py - 2), color, -1)
            cv2.putText(annotated, label, (px + 2, py - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

    # ── 模板保存 ──

    @staticmethod
    def save_crop(hwnd, crop_region, filename, scope, task_name=None, version=None, base64_data=None):
        """截图 → 裁剪 → 保存为 .bmp 模板文件。

        若传入 base64_data（data URL），则直接解码使用，避免二次截图导致画面变化；
        否则从窗口重新截图。"""
        import re as _re

        if base64_data:
            b64 = _re.sub(r'^data:image/\w+;base64,', '', base64_data)
            raw = base64.b64decode(b64)
            arr = np.frombuffer(raw, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("base64 解码失败")
        else:
            img, _ = ScreenCapture.capture_gray(hwnd)

        x1, y1, x2, y2 = crop_region
        x1, x2 = max(0, min(x1, x2)), min(img.shape[1], max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(img.shape[0], max(y1, y2))
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"无效的裁剪区域: {crop_region}")

        cropped = img[y1:y2, x1:x2]
        target_dir = os.path.join(PROJECT_ROOT, "resources", "config", task_name, version, "images") \
            if scope == "task" and task_name and version \
            else os.path.join(PROJECT_ROOT, "resources", "images")
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{filename}.bmp")
        ret, buf = cv2.imencode(".bmp", cropped)
        if not ret:
            raise RuntimeError(f"图像编码失败: {filename}")
        with open(filepath, "wb") as f:
            f.write(buf.tobytes())
        logging.info(f"模板图片已保存: {filepath}")
        return filepath

    # ── 预处理预览 ──

    @staticmethod
    def match_and_visualize(hwnd, args: dict) -> dict:
        """前端预处理弹窗入口：截图 → 匹配 → 可视化。返回 { base64, width, height, matches } 或 { error }。"""
        import re as _re

        mode = args.get("mode", "current")
        crop = args.get("crop")
        preprocess_cfg = {k: v for k, v in args.items() if k in PREPROCESS_KEYS and v is not None}
        logging.info(f"[Matcher] mode={mode}, crop={crop}, pp={preprocess_cfg if preprocess_cfg else '(空)'}")

        try:
            # 解码原图（前端发来的 data URL）
            b64_data = _re.sub(r'^data:image/\w+;base64,', '', args.get("base64", ""))
            img_bytes = base64.b64decode(b64_data)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            original = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if original is None:
                return {"error": "base64 解码失败"}

            # 获取搜索图
            if mode == "current":
                search_img = original
            else:
                _, search_img = ScreenCapture.capture_gray(hwnd)
                original = ScreenCapture.baseline_preprocess(original)

            # 匹配 + 可视化
            pp = preprocess_cfg if preprocess_cfg else None
            processed = ScreenCapture.apply_preprocess(search_img, pp)
            threshold = float(args.get("match_threshold", THRESHOLD))
            matches = TemplateMatcher.match_crop(processed, crop, original, pp, threshold) if crop and isinstance(crop, dict) else []

            result = {"base64": TemplateMatcher.visualize(processed, matches),
                       "width": processed.shape[1], "height": processed.shape[0], "matches": matches}
            logging.info(f"[Matcher] 成功: {result['width']}x{result['height']}, {len(matches)}匹配")
            return result

        except (ValueError, Exception) as e:
            logging.exception(f"[Matcher] 异常: {type(e).__name__}: {e}")
            return {"error": f"{type(e).__name__}: {e}"}


atexit.register(TemplateMatcher.executor.shutdown)
