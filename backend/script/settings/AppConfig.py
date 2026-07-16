import json
import logging
import os

from script.config.Setting import PROJECT_ROOT, SYS_CONFIG_PATH

_defaults_cache = None


def _load_defaults():
    """加载打包的默认配置（内存缓存）。"""
    global _defaults_cache
    if _defaults_cache is not None:
        return _defaults_cache
    path = os.path.join(PROJECT_ROOT, "resources", "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        _defaults_cache = json.load(f)
    return _defaults_cache


def _load_user_settings():
    """加载用户覆盖配置，不存在则返回 {}。"""
    path = os.path.join(SYS_CONFIG_PATH, "settings.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"读取用户设置失败: {e}")
        return {}


def load_merged_settings():
    """合并默认配置与用户覆盖，返回完整 settings dict。"""
    defaults = _load_defaults()
    user = _load_user_settings()
    merged_values = {**(defaults.get("values", {})), **(user.get("values", {}))}
    merged_layout = user.get("layout") if "layout" in user else defaults.get("layout", [])
    return {"values": merged_values, "layout": merged_layout}


def save_user_settings(values):
    """与默认值 diff，只保存差异 key 到用户设置文件。"""
    defaults = _load_defaults()
    default_values = defaults.get("values", {})

    # diff values：只保留与默认值不同的 key
    diff_values = {}
    for k, v in (values or {}).items():
        if k not in default_values or default_values[k] != v:
            diff_values[k] = v

    user = {}
    if diff_values:
        user["values"] = diff_values

    path = os.path.join(SYS_CONFIG_PATH, "settings.json")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(user, f, ensure_ascii=False, indent=2)
        logging.info(f"[Settings] 已保存用户设置到 {path}")
    except Exception as e:
        logging.warning(f"[Settings] 保存用户设置失败: {e}")


def load_plans():
    file_path = os.path.join(PROJECT_ROOT, "resources", "config", "plans.json")
    if not os.path.isfile(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.warning(f"加载计划列表失败: {e}")
        return []
    from script.task import get_repo
    repo = get_repo()
    repo.list_all()
    for plan in data:
        action = plan.get("action", {})
        if action.get("type") == "push_task":
            params = action.get("params", {})
            old_id = params.get("taskId")
            if old_id and not params.get("taskName"):
                cached = repo._cache.get(old_id)
                if cached:
                    params["taskName"] = cached.get("name", "")
                    params["version"] = cached.get("version", None)
                del params["taskId"]
    return data


def save_plans(data):
    file_path = os.path.join(PROJECT_ROOT, "resources", "config", "plans.json")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.warning(f"保存计划列表失败: {e}")
        return False
