import json
import logging
import os

from script.config.Setting import STORAGE_PATH

_CONFIG_PATH = os.path.join(STORAGE_PATH, "Config", "User", "game.json")


def get_game_path() -> str:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("game_exe", "")
    except Exception:
        pass
    return ""


def set_game_path(window) -> dict:
    """弹出文件选择对话框，保存选择的 exe 路径"""
    import webview
    result = window.create_file_dialog(
        webview.FileDialog.OPEN,
        directory="",
        file_types=("可执行文件 (*.exe)",),
    )
    if not result:
        return {"cancelled": True}
    path = result[0] if isinstance(result, (list, tuple)) else result
    if not path or not os.path.isfile(path):
        return {"error": "无效的文件路径"}
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        data = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["game_exe"] = path
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logging.info(f"[GamePath] 已更新游戏路径: {path}")
        return {"success": True, "path": path}
    except Exception as e:
        logging.error(f"[GamePath] 保存失败: {e}")
        return {"error": str(e)}
