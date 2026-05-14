import base64
import hashlib
import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from script.config.Setting import PROJECT_ROOT, USER_CONFIG_PATH

# 全局任务配置缓存: id → 完整配置
_TASK_CONFIG_CACHE = {}


class StaticCommon:

    @staticmethod
    def get_task_config_by_id(task_id):
        """根据 id 从缓存中获取完整任务配置"""
        return _TASK_CONFIG_CACHE.get(task_id)

    @staticmethod
    def load_task_list():
        config_dir = os.path.join(PROJECT_ROOT, "resources", "config")
        tasks = []

        for task_folder in os.listdir(config_dir):
            task_path = os.path.join(config_dir, task_folder)
            if not os.path.isdir(task_path):
                continue

            # 遍历版本子文件夹
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
                # 缓存完整配置
                data["_config_path"] = json_path
                _TASK_CONFIG_CACHE[task_id] = dict(data)

                # 移除不需要的字段（只影响返回给前端的列表）
                for key in ("monitors", "common", "steps", "start"):
                    data.pop(key, None)

            tasks.append(data)
        return tasks

    @staticmethod
    def get_config_list():
        """
        获取任务列表

        该函数扫描用户配置路径下的所有JSON文件，并将文件名（不含扩展名）作为任务名返回

        Returns:
            list: 包含所有任务名的列表，任务名来源于JSON文件的文件名（去除.json后缀）
        """
        taskList = []
        Path(USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        # 遍历用户配置路径下的所有文件，筛选出JSON文件
        for file in os.listdir(USER_CONFIG_PATH):
            if file.endswith(".json"):
                taskList.append(file[:-5])
        return taskList

    @staticmethod
    def save_config(*args):
        """
        保存任务配置到JSON文件

        参数:
            *args: 可变参数列表

                  args[0]: taskConfigName - 任务配置名称(字符串)
                  args[1]: 任务配置参数字典

        返回值:
            无返回值

        功能说明:
            1. 根据配置名称和参数创建任务配置对象
            2. 确保用户配置目录存在
            3. 将配置信息保存为JSON格式文件
        """
        taskConfigName = args[0]

        # 如果配置名称为空则直接返回
        if taskConfigName is None:
            return

        # 确保用户配置目录存在，如果不存在则创建
        Path(USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)

        # 将任务配置保存到JSON文件
        with open(fr"{USER_CONFIG_PATH}\{taskConfigName}.json", "w", encoding="utf-8") as file:
            json.dump(args[1], file, ensure_ascii=False, indent=4)

    @staticmethod
    def load_config(*args):
        """
        加载任务配置信息

        参数:
            *args: 可变参数，第一个参数为任务配置名称

        返回值:
            dict: 配置信息字典，如果加载默认配置则返回默认配置，否则返回从JSON文件读取的配置数据
        """
        taskConfigName = args[0]
        # 从用户配置路径下读取指定的JSON配置文件
        with open(fr"{USER_CONFIG_PATH}\{taskConfigName}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    @staticmethod
    def load_settings():
        # 从用户配置路径下读取指定的JSON配置文件
        with open(fr"{PROJECT_ROOT}\resources\config\settings.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    @staticmethod
    def get_full_task_config(task_id):
        """返回完整任务配置（含 steps/common/monitors/start）"""
        return _TASK_CONFIG_CACHE.get(task_id)

    @staticmethod
    def save_full_task_config(task_id, data):
        """保存完整任务 JSON 回磁盘"""
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

        # 合并数据：保留原有字段，用 data 中的字段覆盖
        merged = {**config, **data}
        merged.pop("id", None)
        merged.pop("_config_path", None)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        # 更新缓存
        merged['id'] = task_id
        merged["_config_path"] = filepath
        _TASK_CONFIG_CACHE[task_id] = merged

    @staticmethod
    def list_actions():
        """返回所有可用的 action 名称"""
        return [
            {"value": "touch", "label": "touch — 识别模板并点击"},
            {"value": "exits", "label": "exits — 检测模板是否存在"},
            {"value": "wait", "label": "wait — 等待模板出现"},
            {"value": "wait_disappear", "label": "wait_disappear — 等待模板消失"},
            {"value": "key_click", "label": "key_click — 发送按键"},
            {"value": "input", "label": "input — 输入文本"},
            {"value": "mouse_click", "label": "mouse_click — 点击坐标"},
            {"value": "set_character", "label": "set_character — 捕获角色头像"},
            {"value": "switch_account", "label": "switch_account — 切换游戏账号"},
            {"value": "{True}", "label": "{True} — 无条件通过"},
        ]

    @staticmethod
    def list_template_images(task_name=None, version=None):
        """扫描全局 + 项目模板图片，返回文件名列表（不含 .bmp 后缀）"""
        images = set()
        # 全局图片
        global_dir = os.path.join(PROJECT_ROOT, "resources", "images")
        if os.path.isdir(global_dir):
            images.update(f[:-4] for f in os.listdir(global_dir) if f.endswith('.bmp'))
        # 项目图片
        if task_name and version:
            task_img_dir = os.path.join(PROJECT_ROOT, "resources", "config", task_name, version, "images")
            if os.path.isdir(task_img_dir):
                images.update(f[:-4] for f in os.listdir(task_img_dir) if f.endswith('.bmp'))
        return sorted(images)

    @staticmethod
    def list_global_common_steps():
        """返回全局 common.json 中的步骤名列表"""
        try:
            file_path = os.path.join(PROJECT_ROOT, "resources", "config", "common.json")
            if not os.path.exists(file_path):
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return sorted(list(data.keys())) if isinstance(data, dict) else []
        except Exception as e:
            logging.warning(f"获取全局公共步骤失败: {e}")
            return []

    @staticmethod
    def load_positions(task_id):
        """加载节点位置缓存"""
        try:
            config = _TASK_CONFIG_CACHE.get(task_id)
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
            logging.warning(f"加载节点位置失败 (task_id={task_id}): {e}")
            return {}

    @staticmethod
    def save_positions(task_id, positions):
        """保存节点位置缓存"""
        try:
            config = _TASK_CONFIG_CACHE.get(task_id)
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

    @staticmethod
    def list_steps_for_task(task_id):
        """返回指定任务的所有步骤名（steps + common 的 key 列表）"""
        config = _TASK_CONFIG_CACHE.get(task_id)
        if not config:
            return []
        steps = list(config.get("steps", {}).keys())
        common = list(config.get("common", {}).keys())
        return sorted(steps + common)

    @staticmethod
    def create_task(name, version, author="", description=""):
        """创建新任务骨架"""
        task_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
        if os.path.exists(task_dir):
            raise FileExistsError(f"任务目录已存在: {task_dir}")

        os.makedirs(task_dir, exist_ok=True)
        os.makedirs(os.path.join(task_dir, "images"), exist_ok=True)

        task_id = hashlib.sha256(f"{name}_{version}".encode('utf-8')).hexdigest()
        task_json = {
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "start": "",
            "steps": {},
            "common": {},
            "monitors": {"loop": [], "interval": 1},
            "values": {},
            "layout": [],
        }
        filepath = os.path.join(task_dir, f"{name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task_json, f, ensure_ascii=False, indent=2)

        task_json["id"] = task_id
        task_json["_config_path"] = filepath
        _TASK_CONFIG_CACHE[task_id] = task_json
        return task_id

    @staticmethod
    def import_task(zip_base64):
        """从 base64 编码的 zip 导入任务"""
        try:
            zip_data = base64.b64decode(zip_base64)
        except Exception:
            return {"error": "base64 解码失败，请检查文件格式"}

        tmpdir = tempfile.mkdtemp(prefix="elves_import_")
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                zf.extractall(tmpdir)

            # 在解压根目录查找任务 JSON（排除 images 子目录）
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

            # 校验必填字段
            name = (task_data.get("name") or "").strip()
            version = (task_data.get("version") or "").strip()
            author = (task_data.get("author") or "").strip()
            if not name:
                return {"error": "任务配置缺少 name 字段"}
            if not version:
                return {"error": "任务配置缺少 version 字段"}
            if not author:
                return {"error": "任务配置缺少 author 字段"}

            # 冲突检测
            dest_dir = os.path.join(PROJECT_ROOT, "resources", "config", name, version)
            if os.path.exists(dest_dir):
                return {"error": f"任务「{name}」版本 {version} 已存在，无法覆盖导入"}

            # 创建目录结构
            images_dir = os.path.join(dest_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            # 复制主配置 JSON
            target_json = os.path.join(dest_dir, f"{name}.json")
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)

            # 复制 positions.json
            src_pos = os.path.join(tmpdir, "positions.json")
            if os.path.isfile(src_pos):
                shutil.copy2(src_pos, os.path.join(dest_dir, "positions.json"))

            # 复制 images
            src_images = os.path.join(tmpdir, "images")
            if os.path.isdir(src_images):
                for fname in os.listdir(src_images):
                    if fname.endswith(".bmp"):
                        shutil.copy2(os.path.join(src_images, fname), os.path.join(images_dir, fname))

            # 写入缓存
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

    @staticmethod
    def load_plans():
        """加载计划任务列表"""
        file_path = os.path.join(PROJECT_ROOT, "resources", "config", "plans.json")
        if not os.path.isfile(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"加载计划列表失败: {e}")
            return []

    @staticmethod
    def save_plans(data):
        """保存计划任务列表"""
        file_path = os.path.join(PROJECT_ROOT, "resources", "config", "plans.json")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.warning(f"保存计划列表失败: {e}")
            return False


