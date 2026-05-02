import hashlib
import json
import os
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


