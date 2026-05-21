import json
import logging
import os
import sys

import webview

from script.api.Api import api
from script.api.JsApi import js
from script.config.Setting import APP_TITLE, VERSION, STORAGE_PATH, PROJECT_ROOT
from script.core.LogManager import setup_logging, read_logs, get_log_files
from script.core.QuickStart import QuickStart
from script.core.ScreenCapture import ScreenCapture
from script.core.Script import Script
from script.core.StaticCommon import StaticCommon
from script.core.FlowEngine import clear_common_cache
from script.account import AccountManager
from script.account.SessionManager import get_session
from script.core.TemplateMatcher import TemplateMatcher
from script.core.Window import Window
from script.util.Utils import Utils
from script.util.TrayIcon import TrayIcon


class App:
    def __init__(self, url):
        setup_logging()
        width, height = Utils.calc_window_size()
        saved_rect = Window.get_saved_rect("main")
        if saved_rect:
            width, height = saved_rect[2] - saved_rect[0], saved_rect[3] - saved_rect[1]
        self.window = webview.create_window(
            f"{APP_TITLE}{VERSION}",
            url,
            js_api=api,
            width=width,
            height=height
        )
        if saved_rect:
            self._restore_main_rect(saved_rect)
        # 存储句柄和对应Script实例的字典
        self._script_instances = {}
        self._lock_states: dict[int, bool] = {}
        self._session = get_session()
        js.init(self.window)
        self._tray: TrayIcon | None = None
        self._qs = QuickStart(self._session, self.window)
        self._setup_tray()
        self.init()

        # 自启动时直接隐藏到托盘
        if "--tray" in sys.argv:
            self.window.hide()

    def _setup_tray(self):
        """初始化系统托盘：关闭窗口 → 隐藏到托盘"""
        self._tray = TrayIcon(APP_TITLE, icon_path=os.path.join(PROJECT_ROOT, "resources", "favicon.ico"))
        self._tray.start_async(
            on_show=lambda: self._show_main_window(),
            on_exit=self._do_exit,
            on_refresh=self._refresh_tray_accounts,
            on_autostart=lambda enabled: Utils.set_autostart(enabled),
            on_reset_close=self._toggle_close_preference,
        )
        self._tray.set_autostart_state(Utils.get_autostart())
        close_pref = self._load_close_preference()
        is_tray = close_pref == "tray"
        logging.info(f"[Setup] initial close_pref={close_pref!r}, tray_checkmark={is_tray}")
        self._tray.set_close_remembered_state(is_tray)
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

    def _get_main_hwnd(self) -> int | None:
        """获取主窗口原生 HWND"""
        try:
            from webview.platforms.winforms import BrowserView
            form = BrowserView.instances.get(self.window.uid)
            if form:
                return int(form.Handle)
        except Exception:
            pass
        return None

    def _restore_main_rect(self, saved_rect):
        """延迟恢复主窗口位置（等 WinForms 窗口就绪）"""
        import threading
        def _do():
            import time
            time.sleep(0.3)
            hwnd = self._get_main_hwnd()
            if hwnd:
                Window.restore_window_rect(hwnd, "main")
        threading.Thread(target=_do, daemon=True).start()

    def _show_main_window(self):
        """显示主窗口并恢复保存的位置"""
        self.window.show()
        hwnd = self._get_main_hwnd()
        if hwnd:
            Window.restore_window_rect(hwnd, "main")

    def _on_window_closing(self) -> bool:
        """窗口关闭：托盘勾 → 最小化到托盘，托盘不勾 → 直接退出"""
        pref = self._load_close_preference()
        logging.info(f"[Close] pref={pref!r}")
        if pref == "tray":
            hwnd = self._get_main_hwnd()
            if hwnd:
                Window.save_window_rect(hwnd, "main")
            self.window.hide()
        else:
            self._do_exit()
        return False

    @staticmethod
    def _close_pref_path() -> str:
        return os.path.join(STORAGE_PATH, "Config", "User", "close_pref.json")

    @staticmethod
    def _load_close_preference() -> str:
        try:
            path = App._close_pref_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f).get("close_action", "")
        except Exception:
            pass
        return ""

    def _toggle_close_preference(self, enabled: bool):
        """托盘菜单：切换关闭偏好。enabled=True 最小化到托盘，False 直接退出"""
        App._save_close_preference("tray" if enabled else "exit")

    @staticmethod
    def _save_close_preference(action: str):
        try:
            path = App._close_pref_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"close_action": action}, f)
        except Exception:
            pass

    @staticmethod
    def _show_close_dialog() -> str:
        """弹出关闭确认对话框（带「不再询问」复选框），返回 'exit' 或 'tray'"""
        import ctypes
        from ctypes import wintypes

        ID_TRAY = 100
        ID_EXIT = 101

        class TASKDIALOG_BUTTON(ctypes.Structure):
            _fields_ = [
                ("nButtonID", ctypes.c_int),
                ("pszButtonText", wintypes.LPCWSTR),
            ]

        class TASKDIALOGCONFIG(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("hwndParent", wintypes.HWND),
                ("hInstance", wintypes.HINSTANCE),
                ("dwFlags", wintypes.DWORD),
                ("dwCommonButtons", wintypes.DWORD),
                ("pszWindowTitle", wintypes.LPCWSTR),
                ("pszMainIcon", wintypes.LPCWSTR),
                ("pszMainInstruction", wintypes.LPCWSTR),
                ("pszContent", wintypes.LPCWSTR),
                ("cButtons", wintypes.UINT),
                ("pButtons", ctypes.POINTER(TASKDIALOG_BUTTON)),
                ("nDefaultButton", ctypes.c_int),
                ("cRadioButtons", wintypes.UINT),
                ("pRadioButtons", ctypes.c_void_p),
                ("nDefaultRadioButton", ctypes.c_int),
                ("pszVerificationText", wintypes.LPCWSTR),
                ("pszExpandedInformation", wintypes.LPCWSTR),
                ("pszExpandedControlText", wintypes.LPCWSTR),
                ("pszCollapsedControlText", wintypes.LPCWSTR),
                ("pszFooterIcon", wintypes.LPCWSTR),
                ("pszFooter", wintypes.LPCWSTR),
                ("pfCallback", ctypes.c_void_p),
                ("lpCallbackData", wintypes.LPARAM),
                ("cxWidth", wintypes.UINT),
            ]

        buttons = (TASKDIALOG_BUTTON * 2)()
        buttons[0] = TASKDIALOG_BUTTON(ID_TRAY, "最小化到托盘，后台运行")
        buttons[1] = TASKDIALOG_BUTTON(ID_EXIT, "退出程序")

        config = TASKDIALOGCONFIG()
        config.cbSize = ctypes.sizeof(TASKDIALOGCONFIG)
        config.dwFlags = 0x0008  # TDF_ALLOW_DIALOG_CANCELLATION
        config.pszWindowTitle = "时雪-创意工坊"
        config.pszMainIcon = 0xFFFD  # TD_INFORMATION_ICON
        config.pszMainInstruction = "关闭程序"
        config.pszContent = "最小化到托盘：程序继续后台运行，可通过托盘图标恢复\n退出程序：立即结束所有任务"
        config.cButtons = 2
        config.pButtons = buttons
        config.nDefaultButton = ID_TRAY
        config.pszVerificationText = "不再询问，记住此选择"

        pn_button = ctypes.c_int()
        pf_checked = ctypes.c_int()

        try:
            ctypes.windll.comctl32.TaskDialogIndirect(
                ctypes.byref(config),
                ctypes.byref(pn_button),
                None,
                ctypes.byref(pf_checked),
            )
            choice = "tray" if pn_button.value == ID_TRAY else "exit"
            logging.info(f"[CloseDlg] TaskDialog choice={choice}, checked={bool(pf_checked.value)}")
            if pf_checked.value:
                App._save_close_preference(choice)
            return choice
        except Exception as e:
            logging.info(f"[CloseDlg] TaskDialogIndirect 不可用({e})，使用 MessageBox 回退")
            MB_YESNO = 0x04
            result = ctypes.windll.user32.MessageBoxW(
                0,
                "关闭 时雪-创意工坊\n\n"
                "是(Y) — 最小化到托盘，后台运行\n"
                "否(N) — 直接退出程序",
                "时雪-创意工坊",
                MB_YESNO | 0x30,
            )
            choice = "tray" if result == 6 else "exit"
            # 回退时也询问是否记住选择
            MB_YESNO2 = 0x04
            remember = ctypes.windll.user32.MessageBoxW(
                0,
                f"是否记住此选择？\n\n以后关闭时将自动{ '最小化到托盘' if choice == 'tray' else '退出程序' }。",
                "时雪-创意工坊",
                MB_YESNO2 | 0x40,
            )
            if remember == 6:
                App._save_close_preference(choice)
            return choice

    def _do_exit(self):
        """真正退出程序"""
        hwnd = self._get_main_hwnd()
        if hwnd:
            Window.save_window_rect(hwnd, "main")
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
        api.on("API:SCRIPT:STOP", self.stop_task)
        api.on("API:SCRIPT:LOCK", self.lock_window)
        api.on("API:SCRIPT:UNLOCK", self.unlock_window)
        api.on("API:SCRIPT:SET_OPACITY", self.set_window_opacity)
        api.on("API:TASK:LOAD:FULL", StaticCommon.get_full_task_config)
        api.on("API:TASK:SAVE:FULL", StaticCommon.save_full_task_config)
        api.on("API:TASK:CREATE", StaticCommon.create_task)
        api.on("API:TASK:DELETE", StaticCommon.delete_task)
        api.on("API:TASK:EXPORT", self.export_task)
        api.on("API:TASK:EXPORT:BATCH", self.export_tasks_batch)
        api.on("API:TASK:IMPORT", StaticCommon.import_task)
        api.on("API:AUTOCOMPLETE:ACTIONS", StaticCommon.list_actions)
        api.on("API:AUTOCOMPLETE:TEMPLATES", StaticCommon.list_template_images)
        api.on("API:AUTOCOMPLETE:STEPS", StaticCommon.list_steps_for_task)
        api.on("API:AUTOCOMPLETE:COMMON:STEPS", StaticCommon.list_global_common_steps)
        api.on("API:COMMON:CACHE:CLEAR", clear_common_cache)
        api.on("API:TASK:LOAD:POSITIONS", StaticCommon.load_positions)
        api.on("API:TASK:SAVE:POSITIONS", StaticCommon.save_positions)
        api.on("API:TEMPLATE:CAPTURE", self.capture_for_template)
        api.on("API:TEMPLATE:CAPTURE:PNG", self.capture_for_template_png)
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
        api.on("API:AUTOSTART:GET", lambda: Utils.get_autostart())
        api.on("API:AUTOSTART:SET", Utils.set_autostart)
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

    def stop_task(self, hwnd):
        if hwnd not in self._script_instances:
            return
        script = self._script_instances[hwnd]
        script.skip_current()
        logging.info(f"[Stop] 跳过当前任务: hwnd={hwnd}")

    def lock_window(self, hwnd):
        """锁定窗口（鼠标穿透），防止用户误触"""
        if hwnd not in self._script_instances:
            logging.warning(f"[Lock] 窗口未绑定: hwnd={hwnd}")
            return
        Window.disable_window(hwnd)
        self._lock_states[hwnd] = True
        logging.info(f"[Lock] 窗口已锁定: hwnd={hwnd}")

    def unlock_window(self, hwnd):
        """解锁窗口，恢复鼠标可交互"""
        if hwnd not in self._script_instances:
            logging.warning(f"[Lock] 窗口未绑定: hwnd={hwnd}")
            return
        Window.enable_window(hwnd)
        self._lock_states[hwnd] = False
        logging.info(f"[Lock] 窗口已解锁: hwnd={hwnd}")

    @staticmethod
    def capture_for_template(hwnd):
        """捕获窗口截图返回 base64 供裁剪弹窗使用"""
        try:
            return ScreenCapture.capture_base64(hwnd)
        except (ValueError, Exception) as e:
            logging.error(f"模板捕获失败: hwnd={hwnd}, error={e}")
            return None

    @staticmethod
    def capture_for_template_png(hwnd):
        """捕获窗口截图返回 PNG base64 供取色器使用"""
        try:
            return ScreenCapture.capture_base64(hwnd, fmt="png")
        except (ValueError, Exception) as e:
            logging.error(f"PNG 截图失败: hwnd={hwnd}, error={e}")
            return None

    @staticmethod
    def save_template_image(hwnd, crop_region, filename, scope, task_name=None, version=None, base64_data=None):
        """截图裁剪保存模板图片。base64_data 为选图时的快照，避免二次截图画面变化。"""
        try:
            return TemplateMatcher.save_crop(hwnd, crop_region, filename, scope, task_name, version, base64_data)
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
        Window.disable_window(hwnd)
        self._lock_states[hwnd] = True
        logging.info(f"[Lock] 窗口已锁定（鼠标穿透）: hwnd={hwnd}")
        self._script(hwnd)

    def unbind(self, hwnd):
        script = self._script_instances.pop(hwnd, None)
        if script:
            script.stop()
        # 无论是否在实例列表中，都确保解锁
        if hwnd in self._lock_states:
            Window.enable_window(hwnd)
            self._lock_states.pop(hwnd, None)
            logging.info(f"[Lock] 窗口已解锁: hwnd={hwnd}")
        else:
            Window.enable_window(hwnd)
        logging.info(f"解绑窗口: hwnd={hwnd}")

    def export_task(self, task_id):
        """导出单个任务为 zip"""
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

    @staticmethod
    def export_tasks_batch(task_ids):
        """批量导出：每个任务独立 zip，弹出文件夹选择器保存"""
        import re as _re
        import tkinter.filedialog as _fd
        import tkinter as _tk

        folder = _fd.askdirectory(title="选择导出文件夹")
        if not folder:
            return {"cancelled": True}

        safe = lambda s: _re.sub(r'[\/\\:*?"<>|]', '_', s or "unknown")
        saved = []
        errors = []
        for tid in task_ids:
            built = StaticCommon.build_task_zip(tid)
            if isinstance(built, dict):
                errors.append(built)
                continue
            buf, default_name = built
            filepath = os.path.join(folder, default_name)
            try:
                with open(filepath, "wb") as f:
                    f.write(buf.getvalue())
                saved.append(default_name)
                logging.info(f"任务导出: {filepath}")
            except OSError as e:
                errors.append({"file": default_name, "error": str(e)})
        return {"saved": saved, "errors": errors}

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
