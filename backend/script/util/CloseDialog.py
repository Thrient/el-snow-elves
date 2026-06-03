import json
import os

from script.config.Setting import STORAGE_PATH


def _close_pref_path() -> str:
    return os.path.join(STORAGE_PATH, "Config", "User", "close_pref.json")


def load_close_preference() -> str:
    try:
        path = _close_pref_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("close_action", "")
    except Exception:
        pass
    return ""


def save_close_preference(action: str):
    try:
        path = _close_pref_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"close_action": action}, f)
    except Exception:
        pass
