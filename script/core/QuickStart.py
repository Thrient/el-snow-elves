"""一键启动：回放账号 + 启动游戏 + 导航到登录界面"""

import json
import logging
import os
import subprocess
import time

import webview

from script.config.Setting import STORAGE_PATH
from script.core.Window import Window
from script.util.Utils import Utils


class QuickStart:
    """一键启动：回放 + 启动游戏 + 导航到登录界面。
    从 App.py 拆出，保持独立可测试。"""

    def __init__(self, session, window):
        self._session = session
        self._window = window

    # ── 公共入口 ──

    def execute(self, account_name: str) -> dict:
        """执行一键启动流程"""
        # Step 1: 启动账号回放
        result = self._session.start_replay(account_name)
        if isinstance(result, dict) and result.get("error"):
            return result
        logging.info(f"[QuickStart] 回放已启动: {account_name}")

        # Step 2: 查找游戏 exe
        game_exe = self._find_game_exe()
        if not game_exe:
            return {"cancelled": True}

        # Step 3: 记录已有窗口，启动游戏
        existing = set(Utils.get_hwnd_by_title())
        logging.info(f"[QuickStart] 启动游戏: {game_exe}")
        subprocess.Popen([game_exe], cwd=os.path.dirname(game_exe))

        # Step 4: 等待新窗口出现（Launcher 会自重启，PID 不可靠）
        hwnd = Utils.wait_for_new_game_window(existing, timeout=120)
        if not hwnd:
            return {"status": "waiting", "message": "游戏已启动，等待窗口出现..."}

        Window.set_window_size(hwnd)

        # Step 5: 导航到登录界面
        self._navigate_to_login(hwnd)
        return {"status": "started", "hwnd": hwnd, "message": "已导航到登录界面，等待代理注入"}

    # ── 内部 ──

    def _find_game_exe(self) -> str | None:
        """查找游戏 exe：已保存路径 → 注册表 → 弹窗选择 → 持久化"""
        config_path = os.path.join(STORAGE_PATH, "Config", "User", "game.json")
        game_exe = Utils.find_game_exe(config_path)

        if game_exe:
            return game_exe

        # 弹窗让用户选择
        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            directory="",
            file_types=("可执行文件 (*.exe)",),
        )
        if not result:
            return None
        game_exe = result[0] if isinstance(result, (list, tuple)) else result
        if not game_exe or not os.path.isfile(game_exe):
            return None

        # 持久化保存
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["game_exe"] = game_exe
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

        return game_exe

    @staticmethod
    def _navigate_to_login(hwnd):
        """模板匹配点击流程：从游戏主界面导航到扫码登录界面"""
        from script.core.InputSimulator import InputSimulator
        from script.core.TemplateMatcher import TemplateMatcher
        from script.functools.Functools import wait_until

        inp = InputSimulator()
        matcher = TemplateMatcher()

        @wait_until(k=1)
        def _wait(*imgs, **kw):
            return matcher.batch_match(*imgs, hwnd=hwnd, **kw)

        logging.info("[QuickStart] 开始导航到登录界面...")

        _wait("按钮首页朕知道了", seconds=120)

        inp.mouse_click(hwnd=hwnd, pos=[610, 630])

        inp.mouse_click(hwnd=Utils.find_window_by_title_and_owner_hwnd("登录", owner_hwnd=hwnd), pos=[180, 365])

        logging.info("[QuickStart] 已导航到登录界面")


