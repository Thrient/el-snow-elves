import base64
import ctypes
import logging
import os
import re
from datetime import datetime

import cv2
import numpy as np
import webview

from script.api.Api import api
from script.api.JsApi import js
from script.config.Setting import APP_TITLE, PROJECT_ROOT, VERSION, STORAGE_PATH
from script.core.LogManager import setup_logging, read_logs, get_log_files
from script.core.ScreenCapture import ScreenCapture
from script.core.Script import Script
from script.core.StaticCommon import StaticCommon
from script.core.Window import Window
from script.util.Utils import Utils

DESIGN_WIDTH = 1335
DESIGN_HEIGHT = 750


def _get_screen_size():
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1920, 1080


def _calc_window_size():
    screen_w, screen_h = _get_screen_size()
    w = screen_w // 2
    h = int(w * DESIGN_HEIGHT / DESIGN_WIDTH)
    if h > screen_h // 2:
        h = screen_h // 2
        w = int(h * DESIGN_WIDTH / DESIGN_HEIGHT)
    return w, h


class App:
    def __init__(self, url):
        width, height = _calc_window_size()
        self.window = webview.create_window(
            f"{APP_TITLE}{VERSION}",
            url,
            js_api=api,
            width=width,
            height=height
        )
        # 存储句柄和对应Script实例的字典
        self._script_instances = {}
        js.init(self.window)
        self.init()

    def init(self):
        api.on("API:SETTINGS:LOAD", StaticCommon.load_settings)
        api.on("API:SCRIPT:SAVE:CONFIG", StaticCommon.save_config)
        api.on("API:SCRIPT:LOAD:CONFIG", StaticCommon.load_config)
        api.on("API:SCRIPT:LOAD:CONFIG:LIST", StaticCommon.get_config_list)
        api.on("API:SCRIPT:LOAD:LIST", StaticCommon.load_task_list)
        api.on("API:SCRIPT:SEARCH", self.search)
        api.on("API:SCRIPT:BIND", self.bind)
        api.on("API:SCRIPT:UNBIND", self.unbind)
        api.on("API:SCRIPT:RESUME", self.resume)
        api.on("API:SCRIPT:PAUSE", self.pause)
        api.on("API:SCRIPT:SCREENSHOT", self.screenshot)
        api.on("API:SCRIPT:SET_OPACITY", self.set_window_opacity)
        api.on("API:TASK:LOAD:FULL", StaticCommon.get_full_task_config)
        api.on("API:TASK:SAVE:FULL", StaticCommon.save_full_task_config)
        api.on("API:TASK:CREATE", StaticCommon.create_task)
        api.on("API:AUTOCOMPLETE:ACTIONS", StaticCommon.list_actions)
        api.on("API:AUTOCOMPLETE:TEMPLATES", StaticCommon.list_template_images)
        api.on("API:AUTOCOMPLETE:STEPS", StaticCommon.list_steps_for_task)
        api.on("API:AUTOCOMPLETE:COMMON:STEPS", StaticCommon.list_global_common_steps)
        api.on("API:TASK:LOAD:POSITIONS", StaticCommon.load_positions)
        api.on("API:TASK:SAVE:POSITIONS", StaticCommon.save_positions)
        api.on("API:TEMPLATE:CAPTURE", self.capture_for_template)
        api.on("API:TEMPLATE:SAVE", self.save_template_image)
        api.on("API:PREPROCESS:APPLY", self.preprocess_apply)
        api.on("API:LOG:READ", read_logs)
        api.on("API:LOG:FILES", get_log_files)
        setup_logging()
        logging.info(f"应用启动: {APP_TITLE} {VERSION}")

    def resume(self, hwnd):
        if hwnd not in self._script_instances:
            return
        script = self._script_instances[hwnd]
        script.resume()

    def pause(self, hwnd):
        if hwnd not in self._script_instances:
            return
        script = self._script_instances[hwnd]
        script.pause()

    @staticmethod
    def screenshot(hwnd):
        try:
            img, _ = ScreenCapture.capture_gray(hwnd)
        except (ValueError, Exception) as e:
            logging.error(f"截图失败: hwnd={hwnd}, error={e}")
            return None

        temp_dir = os.path.join(PROJECT_ROOT, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".bmp"
        filepath = os.path.join(temp_dir, filename)
        cv2.imwrite(filepath, img)
        logging.info(f"截图已保存: {filepath}")
        return filepath

    @staticmethod
    def capture_for_template(hwnd):
        """捕获窗口截图返回 base64 供裁剪弹窗使用"""
        try:
            img, _ = ScreenCapture.capture_gray(hwnd)
        except (ValueError, Exception) as e:
            logging.error(f"模板捕获失败: hwnd={hwnd}, error={e}")
            return None
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return {
            "base64": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}",
            "width": img.shape[1],
            "height": img.shape[0],
        }

    @staticmethod
    def save_template_image(hwnd, crop_region, filename, scope, task_name=None, version=None):
        """
        截图裁剪保存模板图片。
        crop_region: [x1, y1, x2, y2] 相对于游戏窗口客户区的坐标
        filename: 不含扩展名的文件名
        scope: "global" → resources/images/, "task" → resources/config/{task}/{version}/images/
        """
        try:
            img, _ = ScreenCapture.capture_gray(hwnd)
        except (ValueError, Exception) as e:
            logging.error(f"模板截图失败: hwnd={hwnd}, error={e}")
            raise

        x1, y1, x2, y2 = crop_region
        x1, x2 = max(0, min(x1, x2)), min(img.shape[1], max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(img.shape[0], max(y1, y2))
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"无效的裁剪区域: {crop_region}")

        cropped = img[y1:y2, x1:x2]

        if scope == "task" and task_name and version:
            target_dir = os.path.join(PROJECT_ROOT, "resources", "config", task_name, version, "images")
        else:
            target_dir = os.path.join(PROJECT_ROOT, "resources", "images")

        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{filename}.bmp")
        cv2.imwrite(filepath, cropped)
        logging.info(f"模板图片已保存: {filepath}")
        return filepath

    # 预处理相关参数名
    _PREPROCESS_KEYS = {"binarize", "binarize_threshold", "binarize_invert",
                        "adaptive", "adaptive_block", "adaptive_c"}

    # ---------- preprocess_apply helpers ----------

    @staticmethod
    def _decode_base64_image(b64: str):
        """解码前端 data URL 为灰度 numpy 数组。失败返回 None。"""
        b64_data = re.sub(r'^data:image/\w+;base64,', '', b64)
        img_bytes = base64.b64decode(b64_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            logging.info(f"[PREPROCESS] 解码原图: {img.shape[1]}x{img.shape[0]}")
        return img

    @staticmethod
    def _get_search_image(original, mode: str, hwnd: str):
        """mode='current' 返回原图，否则重新截图。返回灰度图或 None。"""
        if mode == "current":
            logging.info("[PREPROCESS] mode=current，在原图上搜索")
            return original
        _, img = ScreenCapture.capture_gray(hwnd)
        logging.info(f"[PREPROCESS] mode=recapture，新截图: {img.shape[1]}x{img.shape[0]}")
        return img

    @staticmethod
    def _non_max_suppression(matches, margin: int = 20, max_kept: int = 50):
        """贪婪 NMS：按置信度降序保留不重叠的匹配点。"""
        sorted_matches = sorted(matches, key=lambda m: -m[0])
        kept = []
        for conf, px, py in sorted_matches:
            too_close = any(
                abs(px - kx) < margin and abs(py - ky) < margin
                for _, kx, ky in kept
            )
            if not too_close:
                kept.append((conf, px, py))
                if len(kept) >= max_kept:
                    break
        return kept

    _MATCH_COLORS = [
        (0.95, (0, 255, 0)),     # 绿色  ≥ 0.95
        (0.9,  (0, 200, 255)),   # 橙色  ≥ 0.9
        (0.0,  (0, 140, 255)),   # 蓝色  <  0.9
    ]

    @classmethod
    def _run_match_template(cls, processed, original, crop, preprocess_cfg, match_threshold):
        """在搜索图上运行模板匹配并标注结果。返回 (标注后图像, match_results 列表)。"""
        x, y = int(crop["x"]), int(crop["y"])
        w, h = int(crop["w"]), int(crop["h"])
        ih, iw = original.shape
        if not (w > 4 and h > 4 and 0 <= x and x + w <= iw and 0 <= y and y + h <= ih):
            logging.warning(f"[PREPROCESS] 无效的 crop: {crop}")
            return processed, []

        # 从原图裁剪模板（与原图相同预处理）
        template_raw = original[y:y+h, x:x+w]
        template = ScreenCapture.apply_preprocess(template_raw, preprocess_cfg)
        logging.info(f"[PREPROCESS] 模板: {template.shape[1]}x{template.shape[0]}，原图({x},{y})")

        # 匹配 + NMS
        result = cv2.matchTemplate(processed, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= match_threshold)
        raw = [(float(result[py, px]), px, py) for py, px in zip(*locations)]
        kept = cls._non_max_suppression(raw)

        # 标注到彩色图
        annotated = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        matches = []
        for confidence, px, py in kept:
            matches.append({"x": int(px), "y": int(py), "w": w, "h": h, "confidence": round(confidence, 4)})
            for thresh, color in cls._MATCH_COLORS:
                if confidence >= thresh:
                    break
            cv2.rectangle(annotated, (px, py), (px + w, py + h), color, 2)
            label = f"{confidence:.3f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (px, py - th - 4), (px + tw + 4, py - 2), color, -1)
            cv2.putText(annotated, label, (px + 2, py - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        logging.info(f"[PREPROCESS] 匹配结果: {len(matches)} 个 (阈值={match_threshold})")
        return annotated, matches

    @staticmethod
    def _encode_result(img, matches):
        """将 numpy 图像编码为 base64 返回 dict。"""
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return {
            "base64": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}",
            "width": img.shape[1],
            "height": img.shape[0],
            "matches": matches,
        }

    @staticmethod
    def preprocess_apply(hwnd, args):
        """
        对截图应用预处理并运行模板匹配，返回标注后的图像。

        args:
            mode: "current" | "recapture"
            base64: 原图 data URL（用于提取模板）
            crop: {x, y, w, h} 框选区域
            match_threshold: 匹配阈值（默认 0.8）
            预处理参数: binarize, binarize_threshold, binarize_invert,
                        adaptive, adaptive_block, adaptive_c
        返回: { base64, width, height, matches } 或 { error }
        """
        logging.info(f"[PREPROCESS] 收到: hwnd={hwnd}, keys={list(args.keys()) if isinstance(args, dict) else type(args).__name__}")

        if not isinstance(args, dict):
            return {"error": f"args 类型错误: {type(args).__name__}"}

        mode = args.get("mode", "current")
        crop = args.get("crop")
        preprocess_cfg = {k: v for k, v in args.items() if k in App._PREPROCESS_KEYS and v is not None}
        logging.info(f"[PREPROCESS] mode={mode}, crop={crop}, pp={preprocess_cfg if preprocess_cfg else '(空)'}")

        try:
            # 解码原图 → 提取模板
            original = App._decode_base64_image(args.get("base64", ""))
            if original is None:
                return {"error": "base64 解码失败"}

            # 获取搜索目标图
            search_img = App._get_search_image(original, mode, hwnd)

            # 预处理 + 匹配
            pp = preprocess_cfg if preprocess_cfg else None
            processed = ScreenCapture.apply_preprocess(search_img, pp)
            if crop and isinstance(crop, dict):
                threshold = float(args.get("match_threshold", 0.8))
                processed, matches = App._run_match_template(processed, original, crop, pp, threshold)
            else:
                matches = []

            result = App._encode_result(processed, matches)
            logging.info(f"[PREPROCESS] 成功: {result['width']}x{result['height']}, {len(matches)}匹配")
            return result

        except (ValueError, Exception) as e:
            logging.error(f"[PREPROCESS] 异常: {type(e).__name__}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {"error": f"{type(e).__name__}: {e}"}

    @staticmethod
    def set_window_opacity(hwnd, opacity):
        try:
            import win32con
            import win32gui
            hwnd_int = int(hwnd)
            style = win32gui.GetWindowLong(hwnd_int, win32con.GWL_EXSTYLE)
            if not (style & win32con.WS_EX_LAYERED):
                win32gui.SetWindowLong(hwnd_int, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
            win32gui.SetLayeredWindowAttributes(hwnd_int, 0, int(opacity), win32con.LWA_ALPHA)
        except Exception as e:
            logging.error(f"设置透明度失败: hwnd={hwnd}, error={e}")

    def search(self):
        winList = []
        for hwnd in Utils.get_hwnd_by_title():
            if hwnd in self._script_instances:
                continue
            try:
                img, _ = ScreenCapture.capture_gray(hwnd=hwnd)
            except (ValueError, Exception):
                continue
            _, buffer = cv2.imencode('.png', img)
            winList.append({
                "hwnd": hwnd,
                "base64": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
            })
        return winList

    def bind(self, hwnd):
        if hwnd in self._script_instances:
            logging.warning(f"窗口已绑定，跳过: hwnd={hwnd}")
            return
        logging.info(f"绑定窗口: hwnd={hwnd}")
        Window.set_window_size(hwnd)
        self._script(hwnd)

    def unbind(self, hwnd):
        if hwnd not in self._script_instances:
            logging.warning(f"窗口未绑定: hwnd={hwnd}")
            return
        script = self._script_instances.pop(hwnd)
        script.stop()
        logging.info(f"解绑窗口: hwnd={hwnd}")

    def _script(self, hwnd):
        script = Script(hwnd)
        self._script_instances[hwnd] = script
        script.start()

    @staticmethod
    def run(debug=False):
        """运行webview窗口应用程序"""
        webview.start(
            ssl=True,
            http_server=True,
            private_mode=False,
            storage_path=STORAGE_PATH,
            debug=debug,
        )
