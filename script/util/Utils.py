import json
import logging
import os
import time
import winreg

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
            if win32gui.GetWindow(target, 4) == owner_hwnd and win32gui.GetWindowText(target) == title:
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

    @staticmethod
    def find_game_exe(config_path: str) -> str | None:
        """自动查找游戏 exe 路径，找不到则弹窗让用户选择，结果持久化"""

        # 1. 读已保存的路径
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f).get("game_exe", "")
                if saved and os.path.isfile(saved):
                    return saved
        except Exception:
            pass

        # 2. 尝试注册表检测
        exe = None
        reg_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        keywords = ["一梦江湖", "wyclx", "yimeng", "Yimeng"]

        for root, subkey in reg_roots:
            if exe:
                break
            try:
                with winreg.OpenKey(root, subkey) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub = winreg.EnumKey(key, i)
                            with winreg.OpenKey(root, f"{subkey}\\{sub}") as sk:
                                name, _ = winreg.QueryValueEx(sk, "DisplayName") if True else ("", "")
                        except Exception:
                            continue
                        try:
                            name = winreg.QueryValueEx(sk, "DisplayName")[0]
                            if any(kw in str(name) for kw in keywords):
                                try:
                                    exe = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                    if exe and os.path.isfile(exe):
                                        break
                                except Exception:
                                    pass
                                try:
                                    install = winreg.QueryValueEx(sk, "InstallLocation")[0]
                                    if install:
                                        for root_dir, _, files in os.walk(install):
                                            for f in files:
                                                if f.endswith(".exe") and any(kw.lower() in f.lower() for kw in ["launcher", "game", "client", "ym", "yj"]):
                                                    exe = os.path.join(root_dir, f)
                                                    break
                                            if exe:
                                                break
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue

        # 3. 注册表没找到 → 返回 None，由调用方弹窗
        if not exe:
            return None

        # 4. 持久化保存
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["game_exe"] = exe
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

        return exe

    @staticmethod
    def wait_for_new_game_window(existing: set[int], timeout: float = 60) -> int | None:
        """等待新的一梦江湖窗口出现（排除已有 hwnd），返回新 hwnd。
        适用于启动器自重启导致 PID 不可靠的场景。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            for hwnd in Utils.get_hwnd_by_title():
                if hwnd not in existing and win32gui.IsWindowVisible(hwnd):
                    return hwnd
            time.sleep(1)
        return None

    @staticmethod
    def calc_window_size():
        """根据设计尺寸和屏幕大小计算窗口宽高"""
        import ctypes
        from script.config.Setting import DESIGN_WIDTH, DESIGN_HEIGHT

        try:
            user32 = ctypes.windll.user32

            sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            sw, sh = 1920, 1080

        w = sw // 2
        h = int(w * DESIGN_HEIGHT / DESIGN_WIDTH)
        if h > sh // 2:
            h = sh // 2
            w = int(h * DESIGN_WIDTH / DESIGN_HEIGHT)
        return w, h

if __name__ == '__main__':
    time.sleep(5)
    hwnd = Utils.get_mouse_window_hwnd()

    child = Utils.find_window_by_title_and_owner_hwnd("MPAY_USER_CENTER", hwnd)
    print(f"parent={hwnd}, child={child}")
