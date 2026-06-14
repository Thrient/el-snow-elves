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

TASK_CONFIG_CACHE = {}


def get_task_config_by_id(task_id):
    return TASK_CONFIG_CACHE.get(task_id)


def load_task_list():
    """返回按 name 合并的任务列表，每个 name 一条，含 versions 列表和 latest 快照。"""
    config_dir = os.path.join(PROJECT_ROOT, "resources", "config")
    by_name = {}

    for task_folder in os.listdir(config_dir):
        task_path = os.path.join(config_dir, task_folder)
        if not os.path.isdir(task_path):
            continue

        name = task_folder
        versions = []
        latest_config = None
        latest_version = (0, 0, 0)

        for version_folder in os.listdir(task_path):
            version_path = os.path.join(task_path, version_folder)
            if not os.path.isdir(version_path):
                continue
            json_path = os.path.join(version_path, f"{name}.json")
            if not os.path.isfile(json_path):
                continue

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("name") != name:
                continue

            version_str = data.get("version", version_folder)
            versions.append(version_str)

            task_id = hashlib.sha256(f"{name}_{version_str}".encode("utf-8")).hexdigest()
            data["id"] = task_id
            data["_config_path"] = json_path
            TASK_CONFIG_CACHE[task_id] = dict(data)

            try:
                v_tuple = tuple(int(x) for x in version_str.split("."))
            except ValueError:
                v_tuple = (0, 0, 0)
            if v_tuple > latest_version:
                latest_version = v_tuple
                latest_config = data

        if not versions:
            continue

        versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)

        merged = {
            "name": name,
            "versions": versions,
            "latest": versions[0],
            "description": latest_config.get("description", "") if latest_config else "",
            "steps": latest_config.get("steps", {}) if latest_config else {},
            "start": latest_config.get("start", "") if latest_config else "",
            "layout": latest_config.get("layout", []) if latest_config else [],
            "values": latest_config.get("values", {}) if latest_config else {},
        }
        by_name[name] = merged

    return list(by_name.values())


def get_full_task_config(name_or_id, version=None):
    if version is not None:
        task_id, config = resolve_task_version(name_or_id, version)
        return config if task_id else None
    # Try cache by ID first (backward compat), then resolve by name -> latest version
    cached = TASK_CONFIG_CACHE.get(name_or_id)
    if cached:
        return cached
    task_id, config = resolve_task_version(name_or_id, None)
    return config if task_id else None


def save_full_task_config(name_or_id, data, version=None):
    if version is not None:
        task_id = hashlib.sha256(f"{name_or_id}_{version}".encode("utf-8")).hexdigest()
    else:
        task_id = name_or_id

    config = TASK_CONFIG_CACHE.get(task_id)
    if not config:
        raise ValueError(f"任务不存在: {task_id}")
    name = config.get("name", "")
    ver = config.get("version", "")
    filepath = os.path.join(PROJECT_ROOT, "resources", "config", name, ver, f"{name}.json")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"任务文件不存在: {filepath}")

    merged = {**config, **data}
    merged.pop("id", None)
    merged.pop("_config_path", None)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    merged["id"] = task_id
    merged["_config_path"] = filepath
    TASK_CONFIG_CACHE[task_id] = merged


def create_task(name, version, description=""):
    task_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
    if os.path.exists(task_dir):
        raise FileExistsError(f"任务目录已存在: {task_dir}")

    os.makedirs(task_dir, exist_ok=True)
    os.makedirs(os.path.join(task_dir, "images"), exist_ok=True)

    task_id = hashlib.sha256(f"{name}_{version}".encode('utf-8')).hexdigest()
    task_json = {
        "name": name, "version": version,
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
    TASK_CONFIG_CACHE[task_id] = task_json
    return task_id


def build_task_zip(name, version=None):
    if version:
        task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
    else:
        task_id, _ = resolve_task_version(name, None)
    if not task_id:
        return {"error": f"任务不存在: {name}"}

    config = get_task_config_by_id(task_id)
    if not config:
        return {"error": f"任务不存在: {task_id}"}

    name = config.get("name", "")
    version = config.get("version", "")
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
    return buf, f"{safe(name)}_{safe(version)}.zip"


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
        if not name:
            return {"error": "任务配置缺少 name 字段"}
        if not version:
            return {"error": "任务配置缺少 version 字段"}

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
        TASK_CONFIG_CACHE[task_id] = task_data

        return {"name": name, "version": version}

    except zipfile.BadZipFile:
        return {"error": "文件不是有效的 ZIP 压缩包"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}
    except OSError as e:
        return {"error": f"文件系统错误: {e}"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def delete_task(name, version=None):
    if version:
        version_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
        task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
        if os.path.isdir(version_dir):
            shutil.rmtree(version_dir, ignore_errors=True)
        TASK_CONFIG_CACHE.pop(task_id, None)
        logging.info(f"[Task] 已删除: {name} v{version}")
        return {"success": True, "name": name, "version": version}
    else:
        task_dir = os.path.join(PROJECT_ROOT, "resources", "config", name)
        if os.path.isdir(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)
        stale = [k for k, v in TASK_CONFIG_CACHE.items() if v.get("name") == name]
        for k in stale:
            TASK_CONFIG_CACHE.pop(k, None)
        logging.info(f"[Task] 已删除整个任务: {name}")
        return {"success": True, "name": name}


def save_as_new_version(name_or_id, new_version, old_version=None):
    """将当前任务保存为新版本（复制整个版本目录 + 更新 version 字段）"""
    if old_version is not None:
        task_id = hashlib.sha256(f"{name_or_id}_{old_version}".encode("utf-8")).hexdigest()
    else:
        task_id = name_or_id

    config = TASK_CONFIG_CACHE.get(task_id)
    if not config:
        return {"error": f"任务不存在: {task_id}"}

    name = config.get("name", "")
    old_version = config.get("version", "")
    if not name or not old_version:
        return {"error": "任务缺少 name 或 version"}

    new_version = (new_version or "").strip()
    if not new_version:
        return {"error": "新版本号不能为空"}
    if new_version == old_version:
        return {"error": f"新版本号与当前版本相同: {new_version}"}

    src_dir = os.path.dirname(config.get("_config_path", ""))
    if not src_dir or not os.path.isdir(src_dir):
        return {"error": "任务目录不存在"}

    dest_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, new_version)
    if os.path.exists(dest_dir):
        return {"error": f"版本 {new_version} 已存在"}

    # 复制整个版本目录
    shutil.copytree(src_dir, dest_dir)

    # 更新新版本 JSON 中的 version 字段
    new_json_path = os.path.join(dest_dir, f"{name}.json")
    with open(new_json_path, "r", encoding="utf-8") as f:
        new_data = json.load(f)
    new_data["version"] = new_version

    with open(new_json_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    # 注册到缓存
    new_task_id = hashlib.sha256(f"{name}_{new_version}".encode("utf-8")).hexdigest()
    new_data["id"] = new_task_id
    new_data["_config_path"] = new_json_path
    TASK_CONFIG_CACHE[new_task_id] = new_data

    logging.info(f"[Task] 保存为新版本: {name} v{old_version} -> v{new_version}")
    return {"success": True, "taskId": new_task_id, "name": name, "version": new_version}


def resolve_task_version(name, version=None):
    """解析任务版本。version=None 时取最高版本。返回 (task_id, config) 或 (None, error)。"""
    task_dir = os.path.join(PROJECT_ROOT, "resources", "config", name)
    if not os.path.isdir(task_dir):
        return None, {"error": f"任务不存在: {name}"}

    if version:
        version_dir = os.path.join(task_dir, version)
        json_path = os.path.join(version_dir, f"{name}.json")
        if not os.path.isfile(json_path):
            return None, {"error": f"版本 {version} 不存在"}
        task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
        cached = TASK_CONFIG_CACHE.get(task_id)
        if cached:
            return task_id, cached
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["id"] = task_id
        data["_config_path"] = json_path
        TASK_CONFIG_CACHE[task_id] = data
        return task_id, data

    # version=None: 取最高版本
    versions = []
    for v_dir in os.listdir(task_dir):
        v_path = os.path.join(task_dir, v_dir)
        if not os.path.isdir(v_path):
            continue
        json_path = os.path.join(v_path, f"{name}.json")
        if os.path.isfile(json_path):
            versions.append(v_dir)

    if not versions:
        return None, {"error": f"任务 {name} 没有可用版本"}

    versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)
    latest = versions[0]
    return resolve_task_version(name, latest)


def list_steps_for_task(task_id):
    config = TASK_CONFIG_CACHE.get(task_id)
    if not config:
        return []
    steps = list(config.get("steps", {}).keys())
    common = list(config.get("common", {}).keys())
    return sorted(steps + common)
