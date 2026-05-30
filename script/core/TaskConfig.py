import json
import os
from pathlib import Path

from script.config.Setting import USER_CONFIG_PATH


def get_config_list():
    Path(USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)
    taskList = []
    for file in os.listdir(USER_CONFIG_PATH):
        if file.endswith(".json"):
            taskList.append(file[:-5])
    return taskList


def save_config(name, data):
    if not name:
        return
    Path(USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)
    with open(fr"{USER_CONFIG_PATH}\{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_config(name):
    with open(fr"{USER_CONFIG_PATH}\{name}.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_config(name):
    if not name:
        return
    path = Path(fr"{USER_CONFIG_PATH}\{name}.json")
    if path.exists():
        path.unlink()
