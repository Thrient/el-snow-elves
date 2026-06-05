import json
import logging
import os
import sys

import webview

from script.api.Api import api
from script.api.JsApi import js
from script.config.Setting import APP_TITLE, VERSION, STORAGE_PATH, PROJECT_ROOT
from script.util.LogManager import setup_logging
from script.core.QuickStart import QuickStart
from script.engine.ScreenCapture import ScreenCapture
from script.window.Script import Script

from script.task_editor.TaskLibrary import build_task_zip


from script.account.AccountManager import AccountManager
from script.account.SessionManager import get_session
from script.engine.TemplateMatcher import TemplateMatcher

from script.util.CacheManager import clear_webview_cache_if_version_changed
from script.window.WindowUtils import Window, calc_window_size, get_hwnd_by_title
from script.util.TrayIcon import TrayIcon
from script.util.CloseDialog import load_close_preference, save_close_preference

from script.util.StartupManager import get_autostart, set_autostart


class App:
    def __init__(self, url):
        setup_logging()
        clear_webview_cache_if_version_changed()
        width, height = calc_window_size()
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
            on_autostart=lambda enabled: set_autostart(enabled),
            on_reset_close=lambda enabled: save_close_preference("tray" if enabled else "exit"),
        )
        self._tray.set_autostart_state(get_autostart())
        close_pref = load_close_preference()
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

    def set_titlebar_theme(self, dark: bool) -> None:
        """设置 Windows 标题栏暗色/亮色主题"""
        logging.info(f"[Theme] set_titlebar_theme called, dark={dark}")
        hwnd = self._get_main_hwnd()
        logging.info(f"[Theme] main hwnd={hwnd}")
        if hwnd is None:
            logging.warning("[Theme] 无法获取主窗口 HWND，标题栏主题设置失败")
            return
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1 if dark else 0)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value),
            )
            logging.info(f"[Theme] DwmSetWindowAttribute hwnd={hwnd} dark={dark} result={result}")
        except Exception as e:
            logging.warning(f"[Theme] DwmSetWindowAttribute 失败: {e}")

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
        pref = load_close_preference()
        logging.info(f"[Close] pref={pref!r}")
        if pref == "tray":
            hwnd = self._get_main_hwnd()
            if hwnd:
                Window.save_window_rect(hwnd, "main")
            self.window.hide()
        else:
            self._do_exit()
        return False

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
        """初始化应用 — 注册所有领域的 IPC 事件处理器。"""
        from script.task_editor import register as reg_task_editor
        from script.task import register as reg_task
        from script.window import register as reg_window
        from script.account import register as reg_account
        from script.plan import register as reg_plan
        from script.settings import register as reg_settings
        from script.log import register as reg_log
        from script.infrastructure import register as reg_infra

        reg_task_editor(api, self)
        reg_task(api, self)
        reg_window(api, self)
        reg_account(api, self)
        reg_plan(api, self)
        reg_settings(api)
        reg_log(api)
        reg_infra(api, self)

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
        for hwnd in get_hwnd_by_title():
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
        built = build_task_zip(task_id)
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
            built = build_task_zip(tid)
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

