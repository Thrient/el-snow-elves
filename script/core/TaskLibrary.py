import base64
import hashlib
import io
import json
import logging
import os
import shutil
import tempfile
import zipfile

from script.config.Setting import PROJECT_ROOT

_TASK_CONFIG_CACHE = {}


def get_task_config_by_id(task_id):
    return _TASK_CONFIG_CACHE.get(task_id)


def load_task_list():
    config_dir = os.path.join(PROJECT_ROOT, "resources", "config")
    tasks = []

    for task_folder in os.listdir(config_dir):
        task_path = os.path.join(config_dir, task_folder)
        if not os.path.isdir(task_path):
            continue

        found = False
        for version_folder in os.listdir(task_path):
            version_path = os.path.join(task_path, version_folder)
            if not os.path.isdir(version_path):
                continue

            json_path = os.path.join(version_path, f"{task_folder}.json")
            if not os.path.isfile(json_path):
                continue

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("name") != task_folder:
                continue

            task_id = hashlib.sha256(f"{data.get('name')}_{data.get('version')}".encode('utf-8')).hexdigest()
            data['id'] = task_id
            data["_config_path"] = json_path
            _TASK_CONFIG_CACHE[task_id] = dict(data)

            found = True
            for key in ("monitors", "common", "steps", "start"):
                data.pop(key, None)

        if found:
            tasks.append(data)
    return tasks


def get_full_task_config(task_id):
    return _TASK_CONFIG_CACHE.get(task_id)


def save_full_task_config(task_id, data):
    config = _TASK_CONFIG_CACHE.get(task_id)
    if not config:
        raise ValueError(f"任务不存在: {task_id}")
    name = config.get("name", "")
    version = config.get("version", "")
    if not name or not version:
        raise ValueError("任务缺少 name 或 version")

    filepath = os.path.join(PROJECT_ROOT, "resources", "config", name, version, f"{name}.json")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"任务文件不存在: {filepath}")

    merged = {**config, **data}
    merged.pop("id", None)
    merged.pop("_config_path", None)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    merged['id'] = task_id
    merged["_config_path"] = filepath
    _TASK_CONFIG_CACHE[task_id] = merged


def create_task(name, version, author="", description=""):
    task_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
    if os.path.exists(task_dir):
        raise FileExistsError(f"任务目录已存在: {task_dir}")

    os.makedirs(task_dir, exist_ok=True)
    os.makedirs(os.path.join(task_dir, "images"), exist_ok=True)

    task_id = hashlib.sha256(f"{name}_{version}".encode('utf-8')).hexdigest()
    task_json = {
        "name": name, "version": version, "author": author,
        "description": description,
        "start": "", "steps": {}, "common": {},
        "monitors": {"loop": [], "interval": 1},
        "values": {}, "layout": [],
    }
    filepath = os.path.join(task_dir, f"{name}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(task_json, f, ensure_ascii=False, indent=2)

    task_json["id"] = task_id
    task_json["_config_path"] = filepath
    _TASK_CONFIG_CACHE[task_id] = task_json
    return task_id


def build_task_zip(task_id):
    config = get_task_config_by_id(task_id)
    if not config:
        return {"error": f"任务不存在: {task_id}"}

    name = config.get("name", "")
    version = config.get("version", "")
    author = config.get("author", "")
    if not name or not version:
        return {"error": "任务缺少 name 或 version"}

    task_dir = os.path.dirname(config.get("_config_path", ""))
    if not task_dir or not os.path.isdir(task_dir):
        return {"error": "任务目录不存在"}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        clean = {k: v for k, v in config.items() if k not in ("id", "_config_path")}
        zf.writestr(f"{name}.json", json.dumps(clean, ensure_ascii=False, indent=2))

        pos_path = os.path.join(task_dir, "positions.json")
        if os.path.isfile(pos_path):
            zf.write(pos_path, "positions.json")

        images_dir = os.path.join(task_dir, "images")
        if os.path.isdir(images_dir):
            for fname in os.listdir(images_dir):
                if fname.endswith(".bmp"):
                    zf.write(os.path.join(images_dir, fname), f"images/{fname}")

    import re as _re
    safe = lambda s: _re.sub(r'[\/\\:*?"<>|]', '_', s or "unknown")
    return buf, f"{safe(name)}_{safe(version)}_{safe(author)}.zip"


def import_task(zip_base64):
    if isinstance(zip_base64, list):
        results = []
        for item in zip_base64:
            results.append(_import_single(item))
        return results
    return _import_single(zip_base64)


def _import_single(zip_base64):
    try:
        zip_data = base64.b64decode(zip_base64)
    except Exception:
        return {"error": "base64 解码失败，请检查文件格式"}

    tmpdir = tempfile.mkdtemp(prefix="elves_import_")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extractall(tmpdir)

        json_files = []
        for fname in os.listdir(tmpdir):
            p = os.path.join(tmpdir, fname)
            if os.path.isfile(p) and fname.endswith(".json") and fname != "positions.json":
                json_files.append(p)

        if not json_files:
            return {"error": "压缩包中未找到任务配置文件"}
        if len(json_files) > 1:
            return {"error": f"压缩包中包含多个 JSON 文件，无法确定任务配置: {[os.path.basename(f) for f in json_files]}"}

        config_path = json_files[0]
        with open(config_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)

        name = (task_data.get("name") or "").strip()
        version = (task_data.get("version") or "").strip()
        author = (task_data.get("author") or "").strip()
        if not name:
            return {"error": "任务配置缺少 name 字段"}
        if not version:
            return {"error": "任务配置缺少 version 字段"}
        if not author:
            return {"error": "任务配置缺少 author 字段"}

        dest_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
        if os.path.exists(dest_dir):
            return {"error": f"任务「{name}」版本 {version} 已存在，无法覆盖导入"}

        images_dir = os.path.join(dest_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        target_json = os.path.join(dest_dir, f"{name}.json")
        with open(target_json, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)

        src_pos = os.path.join(tmpdir, "positions.json")
        if os.path.isfile(src_pos):
            shutil.copy2(src_pos, os.path.join(dest_dir, "positions.json"))

        src_images = os.path.join(tmpdir, "images")
        if os.path.isdir(src_images):
            for fname in os.listdir(src_images):
                if fname.endswith(".bmp"):
                    shutil.copy2(os.path.join(src_images, fname), os.path.join(images_dir, fname))

        task_id = hashlib.sha256(f"{name}_{version}".encode('utf-8')).hexdigest()
        task_data["id"] = task_id
        task_data["_config_path"] = target_json
        _TASK_CONFIG_CACHE[task_id] = task_data

        return {"name": name, "version": version, "author": author}

    except zipfile.BadZipFile:
        return {"error": "文件不是有效的 ZIP 压缩包"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}
    except OSError as e:
        return {"error": f"文件系统错误: {e}"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def delete_task(task_id):
    config = _TASK_CONFIG_CACHE.get(task_id)
    if not config:
        return {"error": f"任务不存在: {task_id}"}
    name = config.get("name", "")
    version = config.get("version", "")
    task_dir = os.path.dirname(config.get("_config_path", ""))
    if task_dir and os.path.isdir(task_dir):
        shutil.rmtree(task_dir, ignore_errors=True)
    _TASK_CONFIG_CACHE.pop(task_id, None)
    logging.info(f"[Task] 已删除: {name} v{version}")
    return {"success": True, "name": name, "version": version}


def list_steps_for_task(task_id):
    config = _TASK_CONFIG_CACHE.get(task_id)
    if not config:
        return []
    steps = list(config.get("steps", {}).keys())
    common = list(config.get("common", {}).keys())
    return sorted(steps + common)
