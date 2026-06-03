"""系统托盘图标 — Shell_NotifyIcon via ctypes，零额外依赖"""

import ctypes
import logging
import threading
from ctypes import wintypes
from typing import Callable, Optional

# Win32 constants
WM_USER = 0x0400
WM_TRAY = WM_USER + 1
NIM_ADD = 0
NIM_DELETE = 2
NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4
NIM_SETFOCUS = 3
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_DESTROY = 0x0002
WS_POPUP = 0x80000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WM_COMMAND = 0x0111
SW_HIDE = 0
SW_SHOW = 5

# 托盘菜单 ID
ID_SHOW = 1001
ID_EXIT = 1002
ID_AUTOSTART = 1003
ID_RESET_CLOSE = 1004
ID_REPLAY_SUBMENU_BASE = 2000  # 回放子菜单项 ID 起点
ID_REFRESH = 2999  # 刷新账号列表


# WNDCLASSW 结构体（ctypes.wintypes 在部分 Python 版本字段不全）
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class TrayIcon:
    """Windows 系统托盘图标"""

    def __init__(self, title: str = "El Snow Elves", icon_path: str | None = None):
        self._title = title
        self._icon_path = icon_path
        self._hwnd = None
        self._thread: threading.Thread | None = None
        self._on_show: Optional[Callable] = None
        self._on_exit: Optional[Callable] = None
        self._on_refresh: Optional[Callable] = None
        self._on_autostart: Optional[Callable] = None
        self._on_reset_close: Optional[Callable] = None
        self._ready = threading.Event()
        self._extra_groups: list[tuple[str, list[tuple[str, Callable]]]] = []
        self._extra_callbacks: list[Callable] = []  # 扁平回调，按序分配 ID
        self._autostart_enabled = False
        self._close_remembered = False

    # ── public API ──

    def start_async(self, on_show: Callable, on_exit: Callable, on_refresh: Optional[Callable] = None, on_autostart: Optional[Callable] = None, on_reset_close: Optional[Callable] = None):
        """在后台线程启动托盘"""
        self._on_show = on_show
        self._on_exit = on_exit
        self._on_refresh = on_refresh
        self._on_autostart = on_autostart
        self._on_reset_close = on_reset_close
        self._thread = threading.Thread(target=self._run, daemon=True, name="TrayIcon")
        self._thread.start()
        self._ready.wait(timeout=5)

    def set_autostart_state(self, enabled: bool):
        """更新开机自启勾选状态"""
        self._autostart_enabled = enabled

    def set_close_remembered_state(self, remembered: bool):
        """更新「记住关闭选择」勾选状态"""
        logging.info(f"[TrayIcon] set_close_remembered_state({remembered})")
        self._close_remembered = remembered

    def set_menu_items(self, groups: list[tuple[str, list[tuple[str, Callable]]]]):
        """设置额外菜单：[(group_label, [(item_label, callback), ...]), ...]
        每个 group 渲染为一个子菜单"""
        self._extra_groups = groups
        self._extra_callbacks = []
        for _, items in groups:
            for _, cb in items:
                self._extra_callbacks.append(cb)

    def stop(self):
        """停止托盘图标"""
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)

    # ── internal ──

    def _run(self):
        try:
            self._create_tray()
        except Exception as e:
            logging.error(f"[TrayIcon] 启动失败: {e}")

    def _create_tray(self):
        """创建隐藏窗口 + 托盘图标 + 消息循环"""
        hinstance = ctypes.windll.kernel32.GetModuleHandleW(None)

        # 注册窗口类
        wnd_class = WNDCLASSW()
        wnd_class.lpfnWndProc = ctypes.cast(WNDPROC(self._wnd_proc), ctypes.c_void_p)
        wnd_class.hInstance = hinstance
        wnd_class.lpszClassName = "ElvesTrayClass"
        atom = ctypes.windll.user32.RegisterClassW(ctypes.byref(wnd_class))
        if not atom:
            logging.error(f"[TrayIcon] RegisterClass 失败: {ctypes.GetLastError()}")
            return

        # 创建隐藏消息窗口
        self._hwnd = ctypes.windll.user32.CreateWindowExW(
            WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
            wintypes.LPCWSTR(atom),
            None,
            WS_POPUP,
            0, 0, 1, 1,
            None, None, hinstance, None,
        )
        if not self._hwnd:
            logging.error(f"[TrayIcon] CreateWindow 失败: {ctypes.GetLastError()}")
            return

        # 关联实例到窗口（用于 wnd_proc 回调）
        _INSTANCES[self._hwnd] = self

        # 添加托盘图标
        if self._icon_path:
            icon_handle = ctypes.windll.user32.LoadImageW(
                0, self._icon_path, 1,  # IMAGE_ICON
                0, 0, 0x00000010 | 0x00000020,  # LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
        else:
            icon_handle = ctypes.windll.user32.LoadIconW(0, 32512)  # IDI_APPLICATION
        self._add_tray_icon(icon_handle or 0)
        self._ready.set()
        logging.info("[TrayIcon] 托盘图标已创建")

        # 消息循环
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        self._remove_tray_icon()
        ctypes.windll.user32.DestroyWindow(self._hwnd)
        _INSTANCES.pop(self._hwnd, None)
        self._hwnd = None
        logging.info("[TrayIcon] 托盘已退出")

    def _add_tray_icon(self, icon_handle):
        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uTimeout", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
            ]

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = icon_handle
        nid.szTip = self._title
        ctypes.windll.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def _remove_tray_icon(self):
        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
            ]
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))

    def _show_menu(self):
        """弹出右键菜单"""
        logging.debug(f"[TrayIcon] _show_menu: autostart={self._autostart_enabled}, close_remembered={self._close_remembered}")
        menu = ctypes.windll.user32.CreatePopupMenu()
        SEP = 0x800  # MF_SEPARATOR

        # 显示主窗口（加粗默认）
        ctypes.windll.user32.AppendMenuW(menu, 0, ID_SHOW, "显示主窗口")
        ctypes.windll.user32.SetMenuDefaultItem(menu, ID_SHOW, 0)

        # ── 账号 ──
        if self._extra_groups:
            accounts_sub = ctypes.windll.user32.CreatePopupMenu()
            cmd_id = ID_REPLAY_SUBMENU_BASE
            for group_label, items in self._extra_groups:
                group_sub = ctypes.windll.user32.CreatePopupMenu()
                for item_label, _ in items:
                    ctypes.windll.user32.AppendMenuW(group_sub, 0, cmd_id, item_label)
                    cmd_id += 1
                ctypes.windll.user32.AppendMenuW(accounts_sub, 0x10, group_sub, group_label)
            ctypes.windll.user32.AppendMenuW(accounts_sub, SEP, 0, "")
            ctypes.windll.user32.AppendMenuW(accounts_sub, 0, ID_REFRESH, "刷新账号列表")
            ctypes.windll.user32.AppendMenuW(menu, 0x10, accounts_sub, "回放账号")

        ctypes.windll.user32.AppendMenuW(menu, SEP, 0, "")

        # ── 设置 ──
        check = 0x8 if self._autostart_enabled else 0  # MF_CHECKED
        ctypes.windll.user32.AppendMenuW(menu, check, ID_AUTOSTART, "开机自启")
        close_check = 0x8 if self._close_remembered else 0
        ctypes.windll.user32.AppendMenuW(menu, close_check, ID_RESET_CLOSE, "最小化到托盘")

        ctypes.windll.user32.AppendMenuW(menu, SEP, 0, "")
        ctypes.windll.user32.AppendMenuW(menu, 0, ID_EXIT, "退出")

        # 获取光标位置
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

        # 设置前台窗口以便菜单能正确关闭
        ctypes.windll.user32.SetForegroundWindow(self._hwnd)
        ctypes.windll.user32.TrackPopupMenu(
            menu, 0, pt.x, pt.y, 0, self._hwnd, None
        )
        ctypes.windll.user32.PostMessageW(self._hwnd, 0, 0, 0)
        ctypes.windll.user32.DestroyMenu(menu)

    # ── 窗口过程 ──

    @staticmethod
    def _wnd_proc(hwnd, msg, wparam, lparam):
        self = _INSTANCES.get(hwnd)
        if not self:
            return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        if msg == WM_TRAY:
            if lparam == WM_LBUTTONUP:
                self._on_show and self._on_show()
            elif lparam == WM_RBUTTONUP:
                self._show_menu()
        elif msg == WM_COMMAND:
            if wparam == ID_SHOW:
                self._on_show and self._on_show()
            elif wparam == ID_AUTOSTART:
                self._autostart_enabled = not self._autostart_enabled
                self._on_autostart and self._on_autostart(self._autostart_enabled)
            elif wparam == ID_RESET_CLOSE:
                self._close_remembered = not self._close_remembered
                self._on_reset_close and self._on_reset_close(self._close_remembered)
            elif wparam == ID_EXIT:
                self._on_exit and self._on_exit()
                self.stop()
            elif wparam == ID_REFRESH:
                self._on_refresh and self._on_refresh()
            elif ID_REPLAY_SUBMENU_BASE <= wparam < ID_REFRESH:
                idx = wparam - ID_REPLAY_SUBMENU_BASE
                if 0 <= idx < len(self._extra_callbacks):
                    try:
                        self._extra_callbacks[idx]()
                    except Exception as e:
                        logging.error(f"[TrayIcon] 菜单回调异常: {e}")
        elif msg == WM_DESTROY:
            ctypes.windll.user32.PostQuitMessage(0)

        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)


# ── 全局 ──

# 窗口过程回调类型
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# 修复 DefWindowProcW 参数类型（避免 64 位 LPARAM 溢出）
ctypes.windll.user32.DefWindowProcW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
]
ctypes.windll.user32.DefWindowProcW.restype = ctypes.c_longlong

# 实例映射（窗口句柄 → TrayIcon 实例，供 wnd_proc 回调查找）
_INSTANCES: dict[int, "TrayIcon"] = {}
