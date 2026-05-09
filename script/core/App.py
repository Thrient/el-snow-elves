import base64
import ctypes
import logging
import os
from datetime import datetime

import cv2
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
