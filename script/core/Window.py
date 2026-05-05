import logging

import logging

import win32con
import win32gui


class Window:

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
    def disable_Window(hwnd):
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
