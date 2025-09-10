import json
import os
from dataclasses import dataclass
from pathlib import Path

from script.config.Config import Config


@dataclass
class TaskConfig:
    __chefIngredientsTags = ['山楂', '土鸡蛋', '番茄', '禽类', '大米', '火腿', '豆腐', '红豆', '精制面粉', '鲜笋',
                             '橙子', '玉米', '牛肉', '糯米', '排骨', '猪肉']
    __chefSeasoningTags = ['白糖', '葱姜蒜', '辣椒', '香料', '陈酒', '黄酒', '盐']

    def __init__(self, **kwargs):
        self.executeList = kwargs.get('executeList', [])
        self.chivalryShoutCount = kwargs.get('chivalryShoutCount', 1)
        self.chivalryNameOrNumber = kwargs.get('chivalryNameOrNumber', '')
        self.model = kwargs.get('model', 'classic')
        # 切换角色
        self.switchCharacterList = kwargs.get('switchCharacterList', [])
        # 每日兑换
        self.dailyExchangeList = kwargs.get('dailyExchangeList', [])
        self.moneyTreeSelect = kwargs.get('moneyTreeSelect', '轻轻摇')
        self.chefIngredientsTags = kwargs.get('chefIngredientsTags', TaskConfig.__chefIngredientsTags)
        self.chefSeasoningTags = kwargs.get('chefSeasoningTags', TaskConfig.__chefSeasoningTags)
        # 世界喊话
        self.ordinaryWorldShouts = kwargs.get('ordinaryWorldShouts', False)
        self.connectedWorldShouts = kwargs.get('connectedWorldShouts', False)
        self.worldShoutsText = kwargs.get('worldShoutsText', '')
        self.worldShoutsCount = kwargs.get('worldShoutsCount', 1)
        # 按键
        self.keyList = kwargs.get('keyList', ['1', '2', '3', '4', '5', '6', '7', '8'])
        # 江湖英雄榜
        self.heroListCount = kwargs.get('heroListCount', 1)
        self.heroListInitiativeExit = kwargs.get('heroListInitiativeExit', False)

    @staticmethod
    def loadConfig(*args):
        """
        加载任务配置信息

        参数:
            *args: 可变参数，第一个参数为任务配置名称

        返回值:
            dict: 配置信息字典，如果加载默认配置则返回默认配置，否则返回从JSON文件读取的配置数据
        """
        taskConfigName = args[0]
        if taskConfigName == "":
            return {}
        if taskConfigName == "默认配置":
            return TaskConfig().__dict__
        # 从用户配置路径下读取指定的JSON配置文件
        with open(fr"{Config.USER_CONFIG_PATH}\{taskConfigName}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return TaskConfig(**data).__dict__

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
    def deleteConfig(*args):
        """
        删除指定的配置文件

        参数:
            *args: 可变参数，第一个参数为配置文件名（不含扩展名）

        返回值:
            无返回值

        功能说明:
            根据传入的文件名参数，删除对应的JSON配置文件
        """
        # 构造配置文件路径并删除文件，如果文件不存在则忽略错误
        Path(f"{Config.USER_CONFIG_PATH}\\{args[0]}.json").unlink(missing_ok=True)

    @staticmethod
    def getTaskList():
        """
        获取任务列表

        该函数扫描用户配置路径下的所有JSON文件，并将文件名（不含扩展名）作为任务名返回

        Returns:
            list: 包含所有任务名的列表，任务名来源于JSON文件的文件名（去除.json后缀）
        """
        taskList = ["默认配置"]
        Path(Config.USER_CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        # 遍历用户配置路径下的所有文件，筛选出JSON文件
        for file in os.listdir(Config.USER_CONFIG_PATH):
            if file.endswith(".json"):
                taskList.append(file[:-5])
        return taskList
