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

    @staticmethod
    def preprocess_apply(hwnd, args):
        """
        对截图应用预处理并运行模板匹配，返回标注后的图像。

        args 字段:
            mode: "current" | "recapture"
            base64: 仅 mode="current" 时传入
            crop: 框选区域 {x, y, w, h}（用作匹配模板）
            match_threshold: 匹配阈值（默认 0.8）
            预处理参数: binarize, binarize_threshold, binarize_invert,
                        adaptive, adaptive_block, adaptive_c
        返回: { base64, width, height, matches: [{x,y,w,h,confidence}] }
        """
        logging.info(f"[PREPROCESS] 收到请求: hwnd={hwnd}, args_keys={list(args.keys()) if isinstance(args, dict) else 'NOT_DICT'}")

        if not isinstance(args, dict):
            logging.error(f"[PREPROCESS] args 不是字典: {type(args)}")
            return None

        mode = args.get("mode", "current")
        crop = args.get("crop", None)

        preprocess_cfg = {k: v for k, v in args.items()
                          if k in App._PREPROCESS_KEYS and v is not None}
        logging.info(f"[PREPROCESS] mode={mode}, crop={crop}, 预处理: {preprocess_cfg if preprocess_cfg else '(空)'}")

        try:
            # 始终解码前端传来的原图（用于提取模板）
            b64 = args.get("base64", "")
            if not b64:
                logging.error("[PREPROCESS] 未提供 base64（模板提取需要原图）")
                return None
            b64_data = re.sub(r'^data:image/\w+;base64,', '', b64)
            img_bytes = base64.b64decode(b64_data)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            original = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if original is None:
                logging.error("[PREPROCESS] 解码 base64 失败")
                return None
            logging.info(f"[PREPROCESS] 解码原图: {original.shape[1]}x{original.shape[0]}")

            # 确定搜索目标图
            if mode == "current":
                search_img = original
                logging.info("[PREPROCESS] mode=current，在原图上搜索")
            else:
                # 重新截图作为搜索目标，模板仍然用原图裁剪
                _, search_img = ScreenCapture.capture_gray(hwnd)
                logging.info(f"[PREPROCESS] mode=recapture，新截图搜索: {search_img.shape[1]}x{search_img.shape[0]}")

            # 对搜索图应用预处理
            processed = ScreenCapture.apply_preprocess(search_img, preprocess_cfg if preprocess_cfg else None)

            # 模板匹配（模板从原图上裁剪）
            match_results = []
            if crop and isinstance(crop, dict):
                x = int(crop.get("x", 0)); y = int(crop.get("y", 0))
                w = int(crop.get("w", 0)); h = int(crop.get("h", 0))
                if w > 4 and h > 4 and x >= 0 and y >= 0 and x + w <= original.shape[1] and y + h <= original.shape[0]:
                    # 从原图上裁剪模板（也应用同样的预处理）
                    template_raw = original[y:y+h, x:x+w]
                    template = ScreenCapture.apply_preprocess(template_raw, preprocess_cfg if preprocess_cfg else None)
                    match_threshold = float(args.get("match_threshold", 0.8))
                    logging.info(f"[PREPROCESS] 模板尺寸: {template.shape[1]}x{template.shape[0]}，从原图({x},{y})裁剪")

                    # 用 matchTemplate 在搜索图上搜索
                    result = cv2.matchTemplate(processed, template, cv2.TM_CCOEFF_NORMED)
                    locations = np.where(result >= match_threshold)
                    h_img, w_img = processed.shape

                    # 转为彩色图以便标注
                    processed_color = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

                    # 非极大值抑制：按置信度排序，去重
                    raw_matches = []
                    for pt_y, pt_x in zip(*locations):
                        confidence = float(result[pt_y, pt_x])
                        raw_matches.append((confidence, pt_x, pt_y))

                    raw_matches.sort(key=lambda m: -m[0])

                    # 去重：距离太近的只保留置信度最高的
                    def boxes_close(b1, b2, margin=20):
                        return (abs(b1[1] - b2[1]) < margin and abs(b1[2] - b2[2]) < margin)

                    kept = []
                    for conf, px, py in raw_matches:
                        too_close = False
                        for _, kx, ky in kept:
                            if boxes_close((conf, px, py), (_, kx, ky)):
                                too_close = True
                                break
                        if not too_close:
                            kept.append((conf, px, py))
                            if len(kept) >= 50:  # 最多画 50 个匹配
                                break

                    for confidence, px, py in kept:
                        match_results.append({
                            "x": int(px), "y": int(py), "w": w, "h": h,
                            "confidence": round(confidence, 4),
                        })
                        # 画矩形和置信度
                        color = (0, 255, 0) if confidence >= 0.95 else (0, 200, 255) if confidence >= 0.9 else (0, 140, 255)
                        cv2.rectangle(processed_color, (px, py), (px + w, py + h), color, 2)
                        label = f"{confidence:.3f}"
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        cv2.rectangle(processed_color, (px, py - th - 4), (px + tw + 4, py - 2), color, -1)
                        cv2.putText(processed_color, label, (px + 2, py - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                    processed = processed_color
                    logging.info(f"[PREPROCESS] 匹配完成: 找到 {len(match_results)} 个匹配点（阈值={match_threshold}）")
                else:
                    logging.warning(f"[PREPROCESS] 无效的 crop 区域: {crop}")

            _, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result = {
                "base64": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}",
                "width": processed.shape[1],
                "height": processed.shape[0],
                "matches": match_results,
            }
            logging.info(f"[PREPROCESS] 返回: {len(result['base64'])}B, {result['width']}x{result['height']}, {len(match_results)}匹配")
            return result

        except (ValueError, Exception) as e:
            logging.error(f"[PREPROCESS] 处理失败: {type(e).__name__}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

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
