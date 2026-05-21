import json
import logging
import os

import win32con
import win32gui


class Window:

    @staticmethod
    def ensure_window_size(hwnd, client_width=1335, client_height=750):
        """检查客户区尺寸，仅在不符合目标值时才调整（轻量，适合高频调用）"""
        try:
            if not win32gui.IsWindow(hwnd):
                return
            rect = win32gui.GetClientRect(hwnd)
            if abs(rect[2] - client_width) <= 1 and abs(rect[3] - client_height) <= 1:
                return
            Window.set_window_size(hwnd)
        except Exception:
            pass

    @staticmethod
    def set_window_size(hwnd):
        """
        根据句柄设置窗口大小，确保客户区大小为1351x789。
        """
        try:
            import ctypes
            from ctypes import wintypes
            # 设置DPI感知（确保系统已启用）
            # noinspection PyUnresolvedReferences
            ctypes.windll.shcore.SetProcessDpiAwareness(1)

            # 获取窗口样式
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            # 获取窗口当前DPI
            # noinspection PyUnresolvedReferences
            dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            if dpi == 0:
                # noinspection PyUnresolvedReferences
                dpi = ctypes.windll.user32.GetDpiForSystem()

            # 目标客户区大小
            client_width, client_height = 1335, 750

            # 计算所需的窗口矩形（初始为客户区大小）
            rect = wintypes.RECT(0, 0, client_width, client_height)
            has_menu = False  # 通常窗口没有菜单栏
            # noinspection PyUnresolvedReferences
            success = ctypes.windll.user32.AdjustWindowRectExForDpi(
                ctypes.byref(rect), style, has_menu, ex_style, dpi)

            if not success:
                # 函数失败时回退到直接设置窗口大小（可能不准）
                logging.warning("DPI 窗口调整失败，使用后备方案")
                current_rect = win32gui.GetWindowRect(hwnd)
                x, y = current_rect[0], current_rect[1]
                win32gui.SetWindowPos(
                    hwnd,
                    0,
                    x,
                    y,
                    client_width,
                    client_height,
                    win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                )
                return

            # 提取窗口总尺寸
            window_width = rect.right - rect.left
            window_height = rect.bottom - rect.top

            # 保持窗口当前位置
            current_rect = win32gui.GetWindowRect(hwnd)
            x, y = current_rect[0], current_rect[1]

            # 设置窗口大小和位置
            win32gui.SetWindowPos(
                hwnd,
                0,
                x,
                y,
                window_width,
                window_height,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )

        except Exception as e:
            logging.error(f"设置窗口大小失败: {e}")

    @staticmethod
    def disable_window(hwnd):
        """
        禁用窗口（点击穿透）
        :param hwnd: 窗口句柄
        :return:
        """
        if not win32gui.IsWindow(hwnd):
            return

        # 添加点击穿透样式
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        )

        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    @staticmethod
    def enable_window(hwnd):
        """
        解除禁用窗口
        :param hwnd: 窗口句柄
        :return:
        """
        if not win32gui.IsWindow(hwnd):
            return

        # 只移除 WS_EX_TRANSPARENT，不影响其他样式
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & ~(win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        )

        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    @staticmethod
    def set_window_opacity(hwnd, opacity):
        """
        设置窗口透明度
        """
        # 确保透明度在有效范围内
        opacity = max(0, min(255, opacity))

        # 设置透明度属性（忽略颜色键，只使用 alpha）
        win32gui.SetLayeredWindowAttributes(hwnd, 0, opacity, win32con.LWA_ALPHA)

        # 强制重绘以立即生效
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    @staticmethod
    def get_saved_rect(name: str) -> tuple | None:
        """读取持久化的窗口 rect，不恢复。返回 (left, top, right, bottom) 或 None"""
        try:
            from script.config.Setting import STORAGE_PATH
            path = os.path.join(STORAGE_PATH, "Config", "User", "window_state.json")
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f).get(name)
            if not saved:
                return None
            return (saved["left"], saved["top"], saved["right"], saved["bottom"])
        except Exception:
            return None

    @staticmethod
    def save_window_rect(hwnd, name: str):
        """持久化窗口位置+尺寸"""
        try:
            from script.config.Setting import STORAGE_PATH
            rect = win32gui.GetWindowRect(hwnd)
            path = os.path.join(STORAGE_PATH, "Config", "User", "window_state.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[name] = {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            logging.info(f"[Window] 已保存窗口状态: {name}")
        except Exception as e:
            logging.info(f"[Window] 保存窗口状态失败: {e}")

    @staticmethod
    def restore_window_rect(hwnd, name: str) -> bool:
        """恢复窗口位置+尺寸，含多屏安全检查。返回 True=成功恢复"""
        try:
            import ctypes
            from script.config.Setting import STORAGE_PATH
            path = os.path.join(STORAGE_PATH, "Config", "User", "window_state.json")
            if not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f).get(name)
            if not saved:
                return False
            left, top, right, bottom = saved["left"], saved["top"], saved["right"], saved["bottom"]

            user32 = ctypes.windll.user32
            vs_x = user32.GetSystemMetrics(76)
            vs_y = user32.GetSystemMetrics(77)
            vs_w = user32.GetSystemMetrics(78)
            vs_h = user32.GetSystemMetrics(79)
            if left >= vs_x + vs_w or top >= vs_y + vs_h or right <= vs_x or bottom <= vs_y:
                logging.info(f"[Window] 保存的窗口位置不可见，跳过恢复: {name}")
                return False

            win32gui.SetWindowPos(hwnd, 0, left, top, right - left, bottom - top,
                                  win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
            logging.info(f"[Window] 已恢复窗口状态: {name}")
            return True
        except Exception as e:
            logging.info(f"[Window] 恢复窗口状态失败: {e}")
            return False
