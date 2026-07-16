import json
import logging
import os

from script.config.Setting import PROJECT_ROOT
from script.task import get_repo


def list_actions():
    return [
        {"value": "touch", "label": "touch — 识别模板并点击"},
        {"value": "exits", "label": "exits — 检测模板是否存在"},
        {"value": "wait", "label": "wait — 等待模板出现"},
        {"value": "wait_disappear", "label": "wait_disappear — 等待模板消失"},
        {"value": "exits_color", "label": "exits_color — 检测颜色是否存在"},
        {"value": "touch_color", "label": "touch_color — 找色并点击"},
        {"value": "wait_color", "label": "wait_color — 等待颜色出现"},
        {"value": "wait_color_disappear", "label": "wait_color_disappear — 等待颜色消失"},
        {"value": "key_click", "label": "key_click — 发送按键"},
        {"value": "input", "label": "input — 输入文本"},
        {"value": "mouse_click", "label": "mouse_click — 点击坐标"},
        {"value": "mouse_drag", "label": "mouse_drag — 拖拽鼠标"},
        {"value": "set_character", "label": "set_character — 捕获角色头像"},
        {"value": "switch_account", "label": "switch_account — 切换游戏账号"},
    ]


def list_template_images(task_name=None, version=None, author="匿名作者"):
    images = set()
    global_dir = os.path.join(PROJECT_ROOT, "resources", "images")
    if os.path.isdir(global_dir):
        images.update(f[:-4] for f in os.listdir(global_dir) if f.endswith('.bmp'))
    if task_name and version:
        repo = get_repo()
        tid, config = repo.resolve(task_name, version, author)
        if config:
            task_dir = os.path.dirname(config.get("_config_path", ""))
            if task_dir:
                task_img_dir = os.path.join(task_dir, "images")
                if os.path.isdir(task_img_dir):
                    images.update(f[:-4] for f in os.listdir(task_img_dir) if f.endswith('.bmp'))
    return sorted(images)


def list_global_common_steps():
    try:
        file_path = os.path.join(PROJECT_ROOT, "resources", "config", "common.json")
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        result = {}
        for name, step in data.items():
            result[name] = dict(step)
        return result
    except Exception as e:
        logging.warning(f"获取全局公共步骤失败: {e}")
        return {}


def load_positions(name, version=None, author="匿名作者"):
    try:
        repo = get_repo()
        task_id, config = repo.resolve(name, version, author)
        if not config:
            return {}
        task_dir = os.path.dirname(config.get("_config_path", ""))
        if not task_dir or not os.path.isdir(task_dir):
            return {}
        pos_path = os.path.join(task_dir, "positions.json")
        if not os.path.exists(pos_path):
            return {}
        with open(pos_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"加载节点位置失败 (name={name}, version={version}): {e}")
        return {}


def save_positions(name, version, positions, author="匿名作者"):
    try:
        repo = get_repo()
        task_id, config = repo.resolve(name, version, author)
        if not config:
            return False
        task_dir = os.path.dirname(config.get("_config_path", ""))
        if not task_dir or not os.path.isdir(task_dir):
            return False
        pos_path = os.path.join(task_dir, "positions.json")
        with open(pos_path, "w", encoding="utf-8") as f:
            json.dump(positions, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.warning(f"保存节点位置失败 (task_id={task_id}): {e}")
        return False
