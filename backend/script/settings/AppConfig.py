import json
import logging
import os

from script.config.Setting import PROJECT_ROOT


def load_settings():
    with open(fr"{PROJECT_ROOT}\resources\config\settings.json", 'r', encoding='utf-8') as f:
        return json.load(f)


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

    # 迁移旧计划格式: taskId -> taskName + version
    from script.task_editor.TaskLibrary import TASK_CONFIG_CACHE, load_task_list as _ltl
    _ltl()
    for plan in data:
        action = plan.get("action", {})
        if action.get("type") == "push_task":
            params = action.get("params", {})
            old_id = params.get("taskId")
            if old_id and not params.get("taskName"):
                cached = TASK_CONFIG_CACHE.get(old_id)
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
