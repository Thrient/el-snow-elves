import logging
import time

import win32api
import win32gui


class Utils:

    @staticmethod
    def get_mouse_window_hwnd():
        """
        通过鼠标当前位置获取窗口句柄

        Returns:
            int: 窗口句柄，如果获取失败则返回None
        """
        # 获取鼠标当前坐标位置
        cursor_pos = win32api.GetCursorPos()
        # 根据坐标获取对应窗口的句柄
        hwnd = win32gui.WindowFromPoint(cursor_pos)
        return hwnd

    @staticmethod
    def get_hwnd_by_mouse_and_title(title="一梦江湖"):
        cursor_pos = win32api.GetCursorPos()
        # 根据坐标获取对应窗口的句柄
        hwnd = win32gui.WindowFromPoint(cursor_pos)

        if win32gui.GetWindowText(hwnd) != title:
            return None
        return hwnd

    @staticmethod
    def get_hwnd_by_title(title="一梦江湖"):

        results = []

        def callback(hwnd, extra):
            # 检查窗口是否可见（可选，根据需求决定是否保留）
            if win32gui.IsWindowVisible(hwnd):
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                # 检查标题是否包含目标字符串（精确匹配可改为 ==）
                if title == window_title:
                    results.append(hwnd)

        win32gui.EnumWindows(callback, None)
        return results

    @staticmethod
    def find_window_by_title_and_owner_hwnd(title: str, owner_hwnd: int) -> int | None:
        """查找属于指定父窗口且标题匹配的子窗口句柄"""
        result: int | None = None

        def callback(target, _):
            nonlocal result
            if win32gui.GetWindow(target, 4) == owner_hwnd and win32gui.GetWindowText(target == title):
                result = target
            return True

        win32gui.EnumWindows(callback, None)
        return result

    @staticmethod
    def clean_duplicate_points(positions, threshold=10):
        """清洗相似的坐标点"""
        cleaned = []
        for pos in positions:
            # 检查当前点是否与已保留点距离小于阈值
            if not any(((pos[0] - ep[0]) ** 2 + (pos[1] - ep[1]) ** 2) ** 0.5 < threshold for ep in cleaned):
                cleaned.append(pos)
        return cleaned

    @staticmethod
    def sendEmit(window, event, data):
        """
        向指定窗口发送自定义事件
        """
        js_code = f"""
            (function() {{
                try {{
                    if (window.$mitt && window.$mitt.emit) {{
                        window.$mitt.emit('{event}', {data});
                    }}
                }} catch (error) {{
                    console.error('Emit error:', error);
                }}
            }})()
        """

        # 如果不需要返回值，可以设为异步执行
        window.run_js(js_code)

    @staticmethod
    def decode_digits(results, digit_map):
        """
        从模板匹配结果中解析出数字序列，并按映射表转换。

        :param results: list of dict，每个字典格式如 {'数字': [(x1,y1), (x2,y2), ...]}
        :param digit_map: dict，映射表，例如 {'零':'0', '一':'1', ...} 或 {'零':'零', ...}
        :return: str，按x坐标顺序拼接后的字符串（已应用映射）
        """
        items = []
        for entry in results:
            for digit, coords in entry.items():
                for coord in coords:
                    items.append((coord[0], digit))
        # 按 x 坐标升序排序
        items.sort(key=lambda pair: pair[0])
        # 应用映射并拼接
        text = ''.join(digit_map[digit] for _, digit in items)
        logging.debug(f"数字解析结果: {text}")
        return text
