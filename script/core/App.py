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
