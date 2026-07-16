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


def _parse_version_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0, 0, 0)


def _make_task_id(name: str, version: str, author: str) -> str:
    return hashlib.sha256(f"{name}_{version}_{author}".encode("utf-8")).hexdigest()


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
        self._migrate_set_to_postset()

    def _migrate_set_to_postset(self):
        """启动时扫描所有任务 JSON，将旧字段名 set 迁移为 postset。"""
        for source in self._sources:
            root = source.root
            if not root.is_dir():
                continue
            for task_dir in os.listdir(root):
                task_path = root / task_dir
                if not task_path.is_dir():
                    continue
                for version_dir in os.listdir(task_path):
                    version_path = task_path / version_dir
                    if not version_path.is_dir():
                        continue
                    for entry in os.listdir(version_path):
                        entry_path = version_path / entry
                        # 新格式: version/author/name.json
                        if entry_path.is_dir():
                            for fn in os.listdir(entry_path):
                                if fn.endswith('.json') and fn != 'positions.json':
                                    self._migrate_file(entry_path / fn)
                        # 旧格式: version/name.json
                        elif entry.endswith('.json') and entry != 'positions.json':
                            self._migrate_file(entry_path)
    @staticmethod
    def _migrate_file(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            changed = False
            for section in ('steps', 'common'):
                for step_def in data.get(section, {}).values():
                    if isinstance(step_def, dict) and 'set' in step_def:
                        step_def['postset'] = step_def.pop('set')
                        changed = True
            if changed:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"[Migration] set→postset: {path}")
        except Exception as e:
            logging.warning(f"[Migration] 跳过 {path}: {e}")

    def _find_conflict(self, name: str, version: str, author: str = "匿名作者") -> bool:
        """检查所有源是否已有同名同版本同作者任务，返回 True/False。"""
        for source in self._sources:
            version_dir = source.root / name / version
            # 新格式优先：<name>/<version>/<author>/<name>.json
            json_path = version_dir / author / f"{name}.json"
            if json_path.is_file():
                return True
            # 旧格式兼容：<name>/<version>/<name>.json（仅当 author 为匿名作者）
            if author == "匿名作者":
                json_path_old = version_dir / f"{name}.json"
                if json_path_old.is_file():
                    return True
        return False

    def list_all(self) -> list[dict]:
        """扫描所有源，按 (name, author) 合并版本列表。
        支持新旧两种目录结构，旧格式自动识别为 author="匿名作者"。"""
        by_key: dict[tuple, dict] = {}  # (name, author) → merged

        for source in reversed(self._sources):
            if not source.root.is_dir():
                continue
            for task_folder in os.listdir(source.root):
                task_path = source.root / task_folder
                if not task_path.is_dir():
                    continue

                name = task_folder
                # 收集该 name 下所有 (version, author, config, json_path)
                entries: list[tuple[tuple, str, dict, str]] = []  # (v_tuple, version_str, config, json_path)

                for version_folder in os.listdir(task_path):
                    version_path = task_path / version_folder
                    if not version_path.is_dir():
                        continue

                    # 新格式：<name>/<version>/<author>/<name>.json
                    for author_folder in os.listdir(version_path):
                        author_path = version_path / author_folder
                        if not author_path.is_dir():
                            continue
                        json_path = author_path / f"{name}.json"
                        if json_path.is_file():
                            with open(json_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if data.get("name") != name:
                                continue
                            if "author" not in data:
                                data["author"] = author_folder
                            version_str = data.get("version", version_folder)
                            v_tuple = _parse_version_tuple(version_str)
                            entries.append((v_tuple, version_str, data, json_path, author_folder))

                    # 旧格式：<name>/<version>/<name>.json → 强制 author="匿名作者"
                    json_path_old = version_path / f"{name}.json"
                    if json_path_old.is_file():
                        with open(json_path_old, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("name") == name:
                            version_str = data.get("version", version_folder)
                            v_tuple = _parse_version_tuple(version_str)
                            author = "匿名作者"
                            data["author"] = "匿名作者"
                            entries.append((v_tuple, version_str, data, json_path_old, author))

                if not entries:
                    continue

                # 按 (name, author) 分组
                groups: dict[str, list] = {}
                for v_tuple, v_str, data, jp, author in entries:
                    groups.setdefault(author, []).append((v_tuple, v_str, data, jp))

                for author, group_items in groups.items():
                    key = (name, author)
                    existing = by_key.get(key, {})

                    versions: list[str] = existing.get("versions", [])
                    latest_config = existing.get("_latest_config")
                    latest_version: tuple = existing.get("_latest_version", (0, 0, 0))

                    for v_tuple, v_str, data, jp in group_items:
                        if v_str not in versions:
                            versions.append(v_str)

                        task_id = _make_task_id(name, v_str, author)
                        data["id"] = task_id
                        data["_config_path"] = str(jp)
                        self._cache[task_id] = dict(data)

                        if v_tuple > latest_version:
                            latest_version = v_tuple
                            latest_config = data

                    if not versions:
                        continue

                    versions.sort(key=lambda v: _parse_version_tuple(v), reverse=True)

                    merged = {
                        "name": name,
                        "author": author,
                        "hub_task_id": latest_config.get("hub_task_id") if latest_config else None,
                        "versions": versions,
                        "latest": versions[0],
                        "description": latest_config.get("description", "") if latest_config else "",
                        "steps": latest_config.get("steps", {}) if latest_config else {},
                        "start": latest_config.get("start", "") if latest_config else "",
                        "layout": latest_config.get("layout", []) if latest_config else [],
                        "values": latest_config.get("values", {}) if latest_config else {},
                        "_latest_config": latest_config,
                        "_latest_version": latest_version,
                    }
                    by_key[key] = merged

        # 清理内部字段后返回
        result = []
        for v in by_key.values():
            v.pop("_latest_config", None)
            v.pop("_latest_version", None)
            result.append(v)
        return result

    def _resolve_version_dir(self, task_dir: Path, name: str, version: str, author: str) -> tuple[str | None, dict | None]:
        """在指定版本目录中按 author 查找任务配置。返回 (task_id, config) 或 (None, None)。"""
        version_dir = task_dir / version
        if not version_dir.is_dir():
            return None, None

        # 新格式：version_dir/author/name.json
        json_path = version_dir / author / f"{name}.json"
        if json_path.is_file():
            task_id = _make_task_id(name, version, author)
            cached = self._cache.get(task_id)
            if cached:
                return task_id, cached
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["id"] = task_id
            data["_config_path"] = str(json_path)
            self._cache[task_id] = data
            return task_id, data

        # 旧格式兼容：version_dir/name.json（仅当 author 为匿名作者）
        if author == "匿名作者":
            json_path_old = version_dir / f"{name}.json"
            if json_path_old.is_file():
                task_id = _make_task_id(name, version, author)
                cached = self._cache.get(task_id)
                if cached:
                    return task_id, cached
                with open(json_path_old, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["id"] = task_id
                data["_config_path"] = str(json_path_old)
                if "author" not in data:
                    data["author"] = author
                self._cache[task_id] = data
                return task_id, data

        return None, None

    def _list_versions_for_author(self, task_dir: Path, name: str, author: str) -> list[str]:
        """扫描目录中符合指定 author 的版本列表。"""
        versions: list[str] = []
        if not task_dir.is_dir():
            return versions
        for v_dir in os.listdir(task_dir):
            v_path = task_dir / v_dir
            if not v_path.is_dir():
                continue
            # 新格式
            if (v_path / author / f"{name}.json").is_file():
                if v_dir not in versions:
                    versions.append(v_dir)
            # 旧格式兼容
            elif author == "匿名作者" and (v_path / f"{name}.json").is_file():
                if v_dir not in versions:
                    versions.append(v_dir)
        versions.sort(key=lambda v: _parse_version_tuple(v), reverse=True)
        return versions

    def resolve(self, name: str, version: str | None = None, author: str = "匿名作者") -> tuple[str | None, dict | None]:
        """按优先级遍历源，返回 (task_id, config)。version=None 取最高版本。"""
        logging.debug(f"[resolve] 入参: name={name} version={version} author={author}")
        for source in self._sources:
            task_dir = source.root / name
            logging.debug(f"[resolve] 检查源: {source.name} root={source.root} task_dir={task_dir} exists={task_dir.is_dir()}")
            if not task_dir.is_dir():
                continue

            if version:
                task_id, config = self._resolve_version_dir(task_dir, name, version, author)
                if task_id:
                    return task_id, config
                continue

            # version=None: 取该源中最高版本
            versions = self._list_versions_for_author(task_dir, name, author)
            logging.debug(f"[resolve] {source.name}: name={name} author={author} versions={versions}")
            if not versions:
                continue

            # 从高到低尝试 resolve
            for v in versions:
                task_id, config = self._resolve_version_dir(task_dir, name, v, author)
                if task_id:
                    return task_id, config

        logging.warning(f"[resolve] 未找到: name={name} version={version} author={author}")
        return None, None

    def get_full_config(self, name_or_id: str, version: str | None = None, author: str = "匿名作者") -> dict | None:
        """公开接口 — 先查缓存再 resolve，返回完整配置或 None。"""
        if version is not None:
            task_id, config = self.resolve(name_or_id, version, author)
            return config if task_id else None
        cached = self._cache.get(name_or_id)
        if cached:
            return cached
        task_id, config = self.resolve(name_or_id, None, author)
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

    def create(self, name: str, version: str, author: str = "匿名作者", description: str = "") -> str:
        """新建任务。检查所有源无冲突后写入用户源。返回 task_id。"""
        # 冲突检查
        conflict = self._find_conflict(name, version, author)
        if conflict:
            raise FileExistsError(f"任务「{name}」版本 {version} 作者 {author} 已存在，无法创建")

        source = self._get_writable_source("user")
        task_dir = source.root / name / version / author
        os.makedirs(task_dir, exist_ok=True)
        os.makedirs(task_dir / "images", exist_ok=True)

        task_id = _make_task_id(name, version, author)
        task_json = {
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "start": "开始执行",
            "steps": {"开始执行": {"action": "", "params": {}}},
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
        logging.info(f"[TaskRepository] 创建任务: {name} v{version} author={author} → {source.name}")
        return task_id

    def save(self, name_or_id: str, data: dict, version: str | None = None, author: str = "匿名作者") -> None:
        """保存任务配置。匹配旧 save_full_task_config(name_or_id, data, version) 签名。"""
        if version is not None:
            task_id = _make_task_id(name_or_id, version, author)
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

    def delete(self, name: str, version: str | None = None, author: str = "匿名作者") -> dict:
        """删除任务。从任务所在源删除。"""
        if version:
            task_id, config = self.resolve(name, version, author)  # resolve 填充缓存
            if not config:
                return {"error": f"任务不存在: {name} v{version} author={author}"}
            config_path = config.get("_config_path", "")
            # 删除 author 子目录
            author_dir = os.path.dirname(config_path) if config_path else ""
            if os.path.isdir(author_dir):
                shutil.rmtree(author_dir, ignore_errors=True)
            # 如果 version 目录变为空，也删除 version 目录
            if author_dir:
                version_dir = os.path.dirname(author_dir)
                if os.path.isdir(version_dir):
                    try:
                        os.rmdir(version_dir)
                    except OSError:
                        pass  # 非空则保留
            self._cache.pop(task_id, None)
            logging.info(f"[TaskRepository] 已删除: {name} v{version} author={author}")
            return {"success": True, "name": name, "version": version, "author": author}
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

    def save_as_new_version(self, name_or_id: str, new_version: str, old_version: str | None = None, author: str = "匿名作者") -> dict:
        """将当前任务保存为新版本（在原源中复制 author 子目录 + 更新 version 字段）。"""
        if old_version is not None:
            task_id = _make_task_id(name_or_id, old_version, author)
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

        # src_dir 是 json 所在目录。旧格式：<root>/<name>/<version>/
        # 新格式：<root>/<name>/<version>/<author>/
        src_dir = os.path.dirname(config.get("_config_path", ""))
        if not src_dir or not os.path.isdir(src_dir):
            return {"error": "任务目录不存在"}

        # 统一往上走到 name 目录：<root>/<name>/
        src_path = Path(config.get("_config_path", ""))
        p = src_path.parent
        while p.name != name:
            p = p.parent
        dest_dir = p / new_version / author
        if dest_dir.exists():
            return {"error": f"版本 {new_version} 作者 {author} 已存在"}

        dest_dir.mkdir(parents=True, exist_ok=True)
        # 复制 src_dir 内容到 dest_dir
        for item in os.listdir(src_dir):
            s = os.path.join(src_dir, item)
            d = str(dest_dir / item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        new_json_path = str(dest_dir / f"{name}.json")
        with open(new_json_path, "r", encoding="utf-8") as f:
            new_data = json.load(f)
        new_data["version"] = new_version

        with open(new_json_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        new_task_id = _make_task_id(name, new_version, author)
        new_data["id"] = new_task_id
        new_data["_config_path"] = new_json_path
        self._cache[new_task_id] = new_data

        logging.info(f"[TaskRepository] 保存为新版本: {name} v{old_ver} → v{new_version} author={author}")
        return {"success": True, "taskId": new_task_id, "name": name, "version": new_version}

    def build_zip(self, name: str, version: str | None = None, author: str = "匿名作者") -> tuple | dict:
        """导出任务为 zip。返回 (BytesIO, filename) 或 error dict。"""
        if version:
            task_id = _make_task_id(name, version, author)
            task_id, config = self.resolve(name, version, author)
        else:
            task_id, config = self.resolve(name, None, author)
        if not task_id:
            return {"error": f"任务不存在: {name}"}

        if not config:
            return {"error": f"任务不存在: {task_id or name}"}

        task_name = config.get("name", name)
        task_version = config.get("version", version or "")
        task_author = config.get("author", author)
        if not task_name or not task_version:
            return {"error": "任务缺少 name 或 version"}

        task_dir = os.path.dirname(config.get("_config_path", ""))
        if not task_dir or not os.path.isdir(task_dir):
            return {"error": "任务目录不存在"}

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # author 是本地标签，导入时重新分配，不导出
            clean = {k: v for k, v in config.items() if k not in ("id", "_config_path", "author", "hub_task_id")}
            zf.writestr(f"{task_name}.json", json.dumps(clean, ensure_ascii=False, indent=2))

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
        # 导出不加 author，文件名保持 <name>_<version>.zip
        return buf, f"{safe(task_name)}_{safe(task_version)}.zip"

    def import_task(self, zip_base64) -> dict:
        """导入任务。接受 {base64, filename} 或纯 base64 字符串。全局冲突检查 → 写入 user 源。"""
        if isinstance(zip_base64, list):
            results = []
            for item in zip_base64:
                results.append(self._import_single(item))
            return results
        return self._import_single(zip_base64)

    def _import_single(self, zip_input) -> dict:
        """导入单个任务。zip_input 可以是 {base64, filename} dict 或纯 base64 字符串。"""
        import base64

        if isinstance(zip_input, dict):
            zip_base64 = zip_input.get("base64", "")
            filename = zip_input.get("filename", "")
        else:
            zip_base64 = zip_input
            filename = ""

        # 从文件名解析 author + task_id：<name>_<version>_<author>[_<task_id>].zip
        parsed_author = "匿名作者"
        parsed_task_id = None
        if filename:
            stem = filename.rsplit(".", 1)[0]  # 去掉扩展名
            parts = stem.split("_", 3)  # 最多分4段：name, version, author, task_id
            if len(parts) >= 3:
                parsed_author = parts[2]
            if len(parts) >= 4:
                try:
                    parsed_task_id = int(parts[3])
                except ValueError:
                    pass

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
            # 文件名解析的作者优先（Hub 下载场景），JSON 中的 author 仅作 fallback
            json_author = (task_data.get("author") or "").strip()
            if parsed_author != "匿名作者":
                author = parsed_author
            elif json_author and json_author != "匿名作者":
                author = json_author
            else:
                author = "匿名作者"
            # hub_task_id: dict 字段优先（程序化传入），文件名解析兜底（手动导入）
            hub_task_id = None
            if isinstance(zip_input, dict):
                hub_task_id = zip_input.get("hub_task_id")
            if not hub_task_id:
                hub_task_id = parsed_task_id

            if not name:
                return {"error": "任务配置缺少 name 字段"}
            if not version:
                return {"error": "任务配置缺少 version 字段"}

            # 全局冲突检查
            conflict = self._find_conflict(name, version, author)
            if conflict:
                return {"error": f"任务「{name}」版本 {version} 作者 {author} 已存在，无法覆盖导入"}

            source = self._get_writable_source("user")
            dest_dir = source.root / name / version / author
            images_dir = dest_dir / "images"
            os.makedirs(images_dir, exist_ok=True)

            target_json = dest_dir / f"{name}.json"
            task_data["author"] = author
            if hub_task_id:
                task_data["hub_task_id"] = hub_task_id
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

            task_id = _make_task_id(name, version, author)
            task_data["id"] = task_id
            task_data["_config_path"] = str(target_json)
            self._cache[task_id] = task_data

            logging.info(f"[TaskRepository] 导入任务: {name} v{version} author={author} → user")
            return {"name": name, "version": version, "author": author}

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
