import base64
import cv2
import webview

from script.api.Api import api
from script.api.JsApi import js
from script.config.Setting import APP_TITLE, VERSION, STORAGE_PATH
from script.core.ScreenCapture import ScreenCapture
from script.core.Script import Script
from script.core.StaticCommon import StaticCommon
from script.util.Utils import Utils


class App:
    def __init__(self, url):
        # 创建窗口
        self.window = webview.create_window(
            f"{APP_TITLE}{VERSION}",
            url,
            js_api=api,
            width=1335,
            height=750
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
        api.on("API:SCRIPT:RESUME", self.resume)
        api.on("API:SCRIPT:PAUSE", self.pause)

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

    def search(self):
        winList = []
        for hwnd in Utils.get_hwnd_by_title():
            if hwnd in self._script_instances:
                continue
            img, _ = ScreenCapture.capture_gray(hwnd=hwnd)
            _, buffer = cv2.imencode('.png', img)
            winList.append({
                "hwnd": hwnd,
                "base64": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
            })
        return winList

    def bind(self, hwnd):
        if hwnd in self._script_instances:
            return
        self._script(hwnd)

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
