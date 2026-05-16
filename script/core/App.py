import logging
import os

import webview

from script.api.Api import api
from script.api.JsApi import js
from script.config.Setting import APP_TITLE, VERSION, STORAGE_PATH, PROJECT_ROOT
from script.core.LogManager import setup_logging, read_logs, get_log_files
from script.core.QuickStart import QuickStart
from script.core.ScreenCapture import ScreenCapture
from script.core.Script import Script
from script.core.StaticCommon import StaticCommon
from script.account import AccountManager
from script.account.SessionManager import get_session
from script.core.TemplateMatcher import TemplateMatcher
from script.core.Window import Window
from script.util.Utils import Utils
from script.util.TrayIcon import TrayIcon


class App:
    def __init__(self, url):
        width, height = Utils.calc_window_size()
        self.window = webview.create_window(
            f"{APP_TITLE}{VERSION}",
            url,
            js_api=api,
            width=width,
            height=height
        )
        # 存储句柄和对应Script实例的字典
        self._script_instances = {}
        self._session = get_session()
        js.init(self.window)
        self._tray: TrayIcon | None = None
        self._qs = QuickStart(self._session, self.window)
        self._setup_tray()
        self.init()

    def _setup_tray(self):
        """初始化系统托盘：关闭窗口 → 隐藏到托盘"""
        self._tray = TrayIcon(APP_TITLE, icon_path=os.path.join(PROJECT_ROOT, "resources", "favicon.ico"))
        self._tray.start_async(
            on_show=lambda: self.window.show(),
            on_exit=self._do_exit,
            on_refresh=self._refresh_tray_accounts,
        )
        # 拦截窗口关闭事件，隐藏到托盘
        self.window.confirm_close = True
        self.window.events.closing += self._on_window_closing

        # 刷新托盘账号菜单
        self._refresh_tray_accounts()

    def _refresh_tray_accounts(self):
        """从账号管理器加载账号列表到托盘菜单"""
        try:
            accounts = AccountManager.list_accounts() or []
        except Exception:
            accounts = []
        groups = []
        for a in accounts:
            name = a.get("name", "")
            if name:
                groups.append((name, [
                    ("回放", lambda n=name: self._tray_replay(n)),
                    ("一键启动", lambda n=name: self._tray_quick_start(n)),
                ]))
        self._tray.set_menu_items(groups)

    def _tray_replay(self, account_name):
        """托盘菜单触发回放"""
        logging.info(f"[Tray] 回放账号: {account_name}")
        import threading
        threading.Thread(target=self._session.start_replay, args=(account_name,), daemon=True).start()

    def _tray_quick_start(self, account_name):
        """托盘菜单触发一键启动"""
        logging.info(f"[Tray] 一键启动: {account_name}")
        import threading
        threading.Thread(target=self._qs.execute, args=(account_name,), daemon=True).start()

    def _on_window_closing(self) -> bool:
        """窗口关闭时隐藏到托盘"""
        self.window.hide()
        return False  # 阻止关闭

    def _do_exit(self):
        """真正退出程序"""
        try:
            self.window.events.closing -= self._on_window_closing
        except Exception:
            pass
        self.window.confirm_close = False
        self.window.destroy()

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
        api.on("API:SCRIPT:SET_OPACITY", self.set_window_opacity)
        api.on("API:TASK:LOAD:FULL", StaticCommon.get_full_task_config)
        api.on("API:TASK:SAVE:FULL", StaticCommon.save_full_task_config)
        api.on("API:TASK:CREATE", StaticCommon.create_task)
        api.on("API:TASK:EXPORT", self.export_task)
        api.on("API:TASK:IMPORT", StaticCommon.import_task)
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
        api.on("API:PLAN:LOAD", StaticCommon.load_plans)
        api.on("API:PLAN:SAVE", StaticCommon.save_plans)
        api.on("API:CRON:TRIGGER", self._on_cron_trigger)
        api.on("API:ACCOUNT:LIST", AccountManager.list_accounts)
        api.on("API:ACCOUNT:LIST:NAMES", AccountManager.list_account_names)
        api.on("API:ACCOUNT:SAVE", AccountManager.save_account)
        api.on("API:ACCOUNT:DELETE", AccountManager.delete_account)
        api.on("API:ACCOUNT:RENAME", AccountManager.rename_account)
        api.on("API:ACCOUNT:RECORD:START", self._session.start_qr_recording)
        api.on("API:ACCOUNT:RECORD:START:CHANNEL", self._session.start_channel_recording)
        api.on("API:ACCOUNT:RECORD:STOP", self._session.stop_recording)
        api.on("API:ACCOUNT:RECORD:STATUS", self._session.recording_status)
        api.on("API:ACCOUNT:REPLAY:START", self._session.start_replay)
        api.on("API:ACCOUNT:QUICK_START", self._qs.execute)
        api.on("API:ACCOUNT:REPLAY:STOP", self._session.stop_replay)
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
    def capture_for_template(hwnd):
        """捕获窗口截图返回 base64 供裁剪弹窗使用"""
        try:
            return ScreenCapture.capture_base64(hwnd)
        except (ValueError, Exception) as e:
            logging.error(f"模板捕获失败: hwnd={hwnd}, error={e}")
            return None

    @staticmethod
    def save_template_image(hwnd, crop_region, filename, scope, task_name=None, version=None):
        """截图裁剪保存模板图片"""
        try:
            return TemplateMatcher.save_crop(hwnd, crop_region, filename, scope, task_name, version)
        except (ValueError, Exception) as e:
            logging.error(f"模板截图失败: hwnd={hwnd}, error={e}")
            raise

    @staticmethod
    def preprocess_apply(hwnd, args):
        """预处理预览：截图 + 匹配 + 可视化标注"""
        logging.info(f"[PREPROCESS] 收到: hwnd={hwnd}, keys={list(args.keys()) if isinstance(args, dict) else type(args).__name__}")
        if not isinstance(args, dict):
            return {"error": f"args 类型错误: {type(args).__name__}"}
        return TemplateMatcher.match_and_visualize(hwnd, args)

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
                cap = ScreenCapture.capture_base64(hwnd, "png")
            except (ValueError, Exception):
                logging.debug(f"窗口截图跳过: {hwnd}")
                continue
            winList.append({"hwnd": hwnd, "base64": cap["base64"]})
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

    def export_task(self, task_id):
        """导出任务为 zip"""
        built = StaticCommon.build_task_zip(task_id)
        if isinstance(built, dict):
            return built
        buf, default_name = built

        result = self.window.create_file_dialog(
            webview.FileDialog.SAVE,
            directory="",
            save_filename=default_name,
            file_types=("ZIP 压缩包 (*.zip)",),
        )
        if not result:
            return {"cancelled": True}

        filepath = result[0] if isinstance(result, tuple) else result
        try:
            with open(filepath, "wb") as f:
                f.write(buf.getvalue())
            logging.info(f"任务导出成功: {filepath}")
            return {"success": True, "path": filepath}
        except OSError as e:
            logging.error(f"导出写入失败: {e}")
            return {"error": f"写入文件失败: {e}"}

    @staticmethod
    def _on_cron_trigger(hwnd, action_type, params):
        logging.info(f"[Cron] 定时触发 hwnd={hwnd} type={action_type} params={params}")

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
