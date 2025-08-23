import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

from script.config.Config import Config


@dataclass
class TaskConfig:
    def __init__(self, **kwargs):
        self.executeList = kwargs.get('executeList', [])
        self.chivalryShoutCount = kwargs.get('chivalryShoutCount', 1)
        self.chivalryNameOrNumber = kwargs.get('chivalryNameOrNumber', '')
        self.model = kwargs.get('model', 'classic')
        self.switchCharacterOne = kwargs.get('switchCharacterOne', False)
        self.switchCharacterTwo = kwargs.get('switchCharacterTwo', False)
        self.switchCharacterThree = kwargs.get('switchCharacterThree', False)
        self.switchCharacterFour = kwargs.get('switchCharacterFour', False)
        self.switchCharacterFive = kwargs.get('switchCharacterFive', False)

    @staticmethod
    def saveConfig(*args):
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

        # 创建任务配置对象
        taskConfig = TaskConfig(**args[1])

        # 确保用户配置目录存在，如果不存在则创建
        Path(Config.USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)

        # 将任务配置保存到JSON文件
        with open(fr"{Config.USER_CONFIG_PATH}\{taskConfigName}.json", "w", encoding="utf-8") as file:
            json.dump(taskConfig.__dict__, file, ensure_ascii=False, indent=4)

    @staticmethod
    def getTaskList():
        """
        获取任务列表

        该函数扫描用户配置路径下的所有JSON文件，并将文件名（不含扩展名）作为任务名返回

        Returns:
            list: 包含所有任务名的列表，任务名来源于JSON文件的文件名（去除.json后缀）
        """
        taskList = []
        # 遍历用户配置路径下的所有文件，筛选出JSON文件
        for file in os.listdir(Config.USER_CONFIG_PATH):
            if file.endswith(".json"):
                taskList.append(file[:-5])
        print(taskList)
        return taskList

