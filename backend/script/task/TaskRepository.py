"""任务仓库 — 多源任务管理，统一读写接口"""
import hashlib
import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from script.config.Setting import PROJECT_ROOT, APP_DATA
from script.task.TaskSource import TaskSource

USER_TASK_PATH = Path(APP_DATA) / "tasks"


class TaskRepository:
    def __init__(self, sources: list[TaskSource] | None = None):
        if sources is None:
            sources = [
                TaskSource(
                    root=Path(PROJECT_ROOT) / "resources" / "config",
                    writable=True,
                    priority=10,
                    name="builtin",
                ),
                TaskSource(
                    root=USER_TASK_PATH,
                    writable=True,
                    priority=5,
                    name="user",
                ),
            ]
        self._sources = sorted(sources, key=lambda s: s.priority, reverse=True)
        self._cache: dict[str, dict] = {}  # task_id → config

    def _find_conflict(self, name: str, version: str) -> TaskSource | None:
        """检查所有源是否已有同名同版本任务，返回冲突的源或 None。"""
        for source in self._sources:
            version_dir = source.root / name / version
            json_path = version_dir / f"{name}.json"
            if json_path.is_file():
                return source
        return None

    def list_all(self) -> list[dict]:
        """扫描所有源，按 name 合并版本列表。
        同名同版本时高优先级覆盖低优先级。返回合并后的任务列表。"""
        by_name: dict[str, dict] = {}

        # 低优先级先处理，高优先级后覆盖
        for source in reversed(self._sources):
            if not source.root.is_dir():
                continue
            for task_folder in os.listdir(source.root):
                task_path = source.root / task_folder
                if not task_path.is_dir():
                    continue

                name = task_folder
                versions: list[str] = []
                latest_config = None
                latest_version = (0, 0, 0)

                for version_folder in os.listdir(task_path):
                    version_path = task_path / version_folder
                    if not version_path.is_dir():
                        continue
                    json_path = version_path / f"{name}.json"
                    if not json_path.is_file():
                        continue

                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if data.get("name") != name:
                        continue

                    version_str = data.get("version", version_folder)
                    versions.append(version_str)

                    task_id = hashlib.sha256(f"{name}_{version_str}".encode("utf-8")).hexdigest()
                    data["id"] = task_id
                    data["_config_path"] = str(json_path)
                    self._cache[task_id] = dict(data)

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

    def resolve(self, name: str, version: str | None = None) -> tuple[str | None, dict | None]:
        """按优先级遍历源，返回 (task_id, config)。version=None 取最高版本。"""
        for source in self._sources:
            task_dir = source.root / name
            if not task_dir.is_dir():
                continue

            if version:
                version_dir = task_dir / version
                json_path = version_dir / f"{name}.json"
                if not json_path.is_file():
                    continue
                task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
                cached = self._cache.get(task_id)
                if cached:
                    return task_id, cached
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["id"] = task_id
                data["_config_path"] = str(json_path)
                self._cache[task_id] = data
                return task_id, data

            # version=None: 取该源中最高版本
            versions = []
            for v_dir in os.listdir(task_dir):
                v_path = task_dir / v_dir
                if not v_path.is_dir():
                    continue
                if (v_path / f"{name}.json").is_file():
                    versions.append(v_dir)

            if not versions:
                continue

            versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)
            return self.resolve(name, versions[0])

        return None, None

    def get_full_config(self, name_or_id: str, version: str | None = None) -> dict | None:
        """公开接口 — 先查缓存再 resolve，返回完整配置或 None。"""
        if version is not None:
            task_id, config = self.resolve(name_or_id, version)
            return config if task_id else None
        cached = self._cache.get(name_or_id)
        if cached:
            return cached
        task_id, config = self.resolve(name_or_id, None)
        return config if task_id else None

    def _get_writable_source(self, prefer: str = "user") -> TaskSource:
        """返回可写源。prefer='user' 时返回 user 源。"""
        for source in self._sources:
            if source.writable and source.name == prefer:
                return source
        # fallback: 返回第一个可写源
        for source in self._sources:
            if source.writable:
                return source
        raise RuntimeError("没有可用的可写任务源")

    def create(self, name: str, version: str, description: str = "") -> str:
        """新建任务。检查所有源无冲突后写入用户源。返回 task_id。"""
        # 冲突检查
        conflict = self._find_conflict(name, version)
        if conflict:
            raise FileExistsError(f"任务「{name}」版本 {version} 已存在（{conflict.name}），无法创建")

        source = self._get_writable_source("user")
        task_dir = source.root / name / version
        os.makedirs(task_dir, exist_ok=True)
        os.makedirs(task_dir / "images", exist_ok=True)

        task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
        task_json = {
            "name": name,
            "version": version,
            "description": description,
            "start": "",
            "steps": {},
            "common": {},
            "monitors": {"loop": [], "interval": 1},
            "values": {},
            "layout": [],
        }
        filepath = task_dir / f"{name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task_json, f, ensure_ascii=False, indent=2)

        task_json["id"] = task_id
        task_json["_config_path"] = str(filepath)
        self._cache[task_id] = task_json
        logging.info(f"[TaskRepository] 创建任务: {name} v{version} → {source.name}")
        return task_id

    def save(self, name_or_id: str, data: dict, version: str | None = None) -> None:
        """保存任务配置。匹配旧 save_full_task_config(name_or_id, data, version) 签名。"""
        if version is not None:
            task_id = hashlib.sha256(f"{name_or_id}_{version}".encode("utf-8")).hexdigest()
        else:
            task_id = name_or_id

        config = self._cache.get(task_id)
        if not config:
            raise ValueError(f"任务不存在: {task_id}")

        filepath = config.get("_config_path")
        if not filepath or not os.path.isfile(filepath):
            raise FileNotFoundError(f"任务文件不存在: {filepath}")

        merged = {**config, **data}
        merged.pop("id", None)
        merged.pop("_config_path", None)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        merged["id"] = task_id
        merged["_config_path"] = filepath
        self._cache[task_id] = merged

    def delete(self, name: str, version: str | None = None) -> dict:
        """删除任务。从任务所在源删除。"""
        if version:
            task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
            task_id, config = self.resolve(name, version)  # resolve 填充缓存
            if not config:
                return {"error": f"任务不存在: {name} v{version}"}
            version_dir = os.path.dirname(config.get("_config_path", ""))
            if os.path.isdir(version_dir):
                shutil.rmtree(version_dir, ignore_errors=True)
            self._cache.pop(task_id, None)
            logging.info(f"[TaskRepository] 已删除: {name} v{version}")
            return {"success": True, "name": name, "version": version}
        else:
            # 删除整个任务（所有版本），从找到的第一个源删
            for source in self._sources:
                task_dir = source.root / name
                if task_dir.is_dir():
                    shutil.rmtree(task_dir, ignore_errors=True)
                    stale = [k for k, v in self._cache.items() if v.get("name") == name]
                    for k in stale:
                        self._cache.pop(k, None)
                    logging.info(f"[TaskRepository] 已删除整个任务: {name} (source={source.name})")
                    return {"success": True, "name": name}
            return {"error": f"任务不存在: {name}"}

    def save_as_new_version(self, name_or_id: str, new_version: str, old_version: str | None = None) -> dict:
        """将当前任务保存为新版本（在原源中复制版本目录 + 更新 version 字段）。"""
        if old_version is not None:
            task_id = hashlib.sha256(f"{name_or_id}_{old_version}".encode("utf-8")).hexdigest()
        else:
            task_id = name_or_id

        config = self._cache.get(task_id)
        if not config:
            return {"error": f"任务不存在: {task_id}"}

        name = config.get("name", "")
        old_ver = config.get("version", "")
        if not name or not old_ver:
            return {"error": "任务缺少 name 或 version"}

        new_version = (new_version or "").strip()
        if not new_version:
            return {"error": "新版本号不能为空"}
        if new_version == old_ver:
            return {"error": f"新版本号与当前版本相同: {new_version}"}

        src_dir = os.path.dirname(config.get("_config_path", ""))
        if not src_dir or not os.path.isdir(src_dir):
            return {"error": "任务目录不存在"}

        # 新版本放在同一源的 name/new_version 下
        parent_dir = os.path.dirname(src_dir)  # .../<name>/
        dest_dir = os.path.join(parent_dir, new_version)
        if os.path.exists(dest_dir):
            return {"error": f"版本 {new_version} 已存在"}

        shutil.copytree(src_dir, dest_dir)

        new_json_path = os.path.join(dest_dir, f"{name}.json")
        with open(new_json_path, "r", encoding="utf-8") as f:
            new_data = json.load(f)
        new_data["version"] = new_version

        with open(new_json_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        new_task_id = hashlib.sha256(f"{name}_{new_version}".encode("utf-8")).hexdigest()
        new_data["id"] = new_task_id
        new_data["_config_path"] = new_json_path
        self._cache[new_task_id] = new_data

        logging.info(f"[TaskRepository] 保存为新版本: {name} v{old_ver} → v{new_version}")
        return {"success": True, "taskId": new_task_id, "name": name, "version": new_version}

    def build_zip(self, name: str, version: str | None = None) -> tuple | dict:
        """导出任务为 zip。返回 (BytesIO, filename) 或 error dict。"""
        if version:
            task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
        else:
            task_id, _ = self.resolve(name, None)
        if not task_id:
            return {"error": f"任务不存在: {name}"}

        config = self._cache.get(task_id)
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
        safe = lambda s: _re.sub(r'[\/\\:*?"<>|]', "_", s or "unknown")
        return buf, f"{safe(name)}_{safe(version)}.zip"

    def import_task(self, zip_base64) -> dict:
        """导入任务。全局冲突检查 → 写入 user 源。"""
        if isinstance(zip_base64, list):
            results = []
            for item in zip_base64:
                results.append(self._import_single(item))
            return results
        return self._import_single(zip_base64)

    def _import_single(self, zip_base64) -> dict:
        import base64
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

            # 全局冲突检查
            conflict = self._find_conflict(name, version)
            if conflict:
                return {"error": f"任务「{name}」版本 {version} 已存在（{conflict.name}），无法覆盖导入"}

            source = self._get_writable_source("user")
            dest_dir = source.root / name / version
            images_dir = dest_dir / "images"
            os.makedirs(images_dir, exist_ok=True)

            target_json = dest_dir / f"{name}.json"
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)

            src_pos = os.path.join(tmpdir, "positions.json")
            if os.path.isfile(src_pos):
                shutil.copy2(src_pos, str(dest_dir / "positions.json"))

            src_images = os.path.join(tmpdir, "images")
            if os.path.isdir(src_images):
                for fname in os.listdir(src_images):
                    if fname.endswith(".bmp"):
                        shutil.copy2(os.path.join(src_images, fname), str(images_dir / fname))

            task_id = hashlib.sha256(f"{name}_{version}".encode("utf-8")).hexdigest()
            task_data["id"] = task_id
            task_data["_config_path"] = str(target_json)
            self._cache[task_id] = task_data

            logging.info(f"[TaskRepository] 导入任务: {name} v{version} → user")
            return {"name": name, "version": version}

        except zipfile.BadZipFile:
            return {"error": "文件不是有效的 ZIP 压缩包"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON 解析失败: {e}"}
        except OSError as e:
            return {"error": f"文件系统错误: {e}"}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def list_steps_for_task(self, task_id: str) -> list[str]:
        """返回任务中所有步骤名称（steps + common keys）。"""
        config = self._cache.get(task_id)
        if not config:
            return []
        steps = list(config.get("steps", {}).keys())
        common = list(config.get("common", {}).keys())
        return sorted(steps + common)
