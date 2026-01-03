"""
多窗口同步器核心模块 - 完整实现
专注窗口同步功能，外部通过句柄添加窗口
"""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Set

import keyboard
import mouse
import win32gui

from script.window.WindowInteractor import WindowInteractor

# 配置日志
logger = logging.getLogger(__name__)


class WindowSynchronizer:
    """多窗口同步器核心类 - 完整实现"""

    # 线程池
    CV_POOL = ThreadPoolExecutor(
        max_workers=max(2, min(6, os.cpu_count()))
    )

    def __init__(self):
        super().__init__()
        # 窗口句柄集合
        self.windows: Set[int] = set()

        self.window_interactors = {}

        self.cace = ()

        # 运行状态
        self.is_running: bool = False

        # 线程控制
        self._stop_event = threading.Event()

        # 同步选项
        self.sync_options = {
            'scroll': True,  # 滚动同步
            'clicks': True,  # 鼠标点击同步（谨慎使用）
            'keyboard': True,  # 键盘同步（谨慎使用）
            'movement': False,  # 鼠标移动同步
        }

        # 性能选项
        self.performance = {
            'scroll_sensitivity': 1.0,  # 滚动灵敏度
            'sync_delay': 0.01,  # 同步延迟（秒）
            'scroll_cooldown': 0.05,  # 滚动冷却时间（防抖）
            'keyboard_delay': 0.02,  # 键盘同步延迟
            'click_delay': 0.03,  # 点击同步延迟
        }

        # 线程锁
        self._lock = threading.RLock()

        self.setup_hooks()

    def add_window(self, hwnd: int) -> bool:
        """添加窗口到同步器"""
        with self._lock:
            if not win32gui.IsWindow(hwnd):
                logger.error(f"无效的窗口句柄: {hwnd}")
                return False

            if hwnd in self.windows:
                logger.warning(f"窗口已存在于同步器中: {hwnd}")
                return False

            self.windows.add(hwnd)

            self.window_interactors[hwnd] = WindowInteractor(hwnd)

            logger.info(f"已添加窗口: {hwnd})")

            return True

    def remove_window(self, hwnd: int) -> bool:
        """从同步器中移除窗口"""
        with self._lock:
            if hwnd not in self.windows:
                logger.warning(f"窗口不存在于同步器中: {hwnd}")
                return False
            self.windows.discard(hwnd)
            del self.window_interactors[hwnd]
            return True

    def setup_hooks(self):
        """设置全局钩子"""
        # 键盘钩子
        keyboard.on_press(self.on_key_press)

        # 鼠标钩子
        mouse.on_button(self.on_mouse_down, (), ['left'], ['down'])
        mouse.on_button(self.on_mouse_up, (), ['left'], ['up'])
        # mouse.on_right_click(self.on_mouse_right_click)
        # mouse.on_middle_click(self.on_mouse_middle_click)
        # mouse.on_double_click(self.on_mouse_double_click)

    def on_key_press(self, event):
        with self._lock:
            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd not in self.windows:
                return

            [
                self.CV_POOL.submit(
                    self.window_interactors[hwnd].click_key,
                    event.name.upper(),
                )
                for hwnd in self.windows
                if hwnd != current_hwnd
            ]

    def on_mouse_down(self):

        with self._lock:
            x, y = mouse.get_position()
            print(x, y)

            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd not in self.windows:
                return

            self.cace = self._to_window_coordinates(current_hwnd, x, y)

    def on_mouse_up(self):

        with self._lock:
            x, y = mouse.get_position()

            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd not in self.windows:
                return

            [
                self.CV_POOL.submit(
                    self.window_interactors[hwnd].mouse_move,
                    self.cace,
                    self._to_window_coordinates(current_hwnd, x, y)
                )
                for hwnd in self.windows
                if hwnd != current_hwnd
            ]

    @staticmethod
    def _to_window_coordinates(hwnd, screen_x, screen_y):
        """
        将屏幕坐标转换为窗口客户区坐标
        """
        # 获取窗口位置和大小
        rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)

        # 计算窗口边框和标题栏大小
        border_width = (rect[2] - rect[0] - client_rect[2]) // 2
        title_height = (rect[3] - rect[1] - client_rect[3]) - border_width

        x = screen_x - rect[0] - border_width
        y = screen_y - rect[1] - title_height

        # 转换为窗口客户区坐标
        return x, y

    def wait_and_exit(self):
        """等待退出"""
        print("钩子已启动，按 ESC 退出")
        keyboard.wait('esc')


# 使用示例
if __name__ == "__main__":
    # 创建同步器
    sync = WindowSynchronizer()

    sync.add_window(1968068)
    sync.add_window(198358)
    sync.add_window(1049814)

    sync.wait_and_exit()
