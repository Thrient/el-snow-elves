from script.task.classic.AcquisitionTask import AcquisitionTask
from script.task.classic.BountyMissionsTask import BountyMissionsTask
from script.task.classic.BreakBanTask import BreakBanTask
from script.task.classic.ChivalryShoutTask import ChivalryShoutTask
from script.task.classic.DailyCopiesTask import DailyCopiesTask
from script.task.classic.DailyRedemptionTask import DailyRedemptionTask
from script.task.classic.DoorBanTask import DoorBanTask
from script.task.classic.FactionTask import FactionTask
from script.task.classic.HeroListTask import HeroListTask
from script.task.classic.HexagramDayTask import HexagramDayTask
from script.task.classic.LessonTask import LessonTask
from script.task.classic.MerchantLakeTask import MerchantLakeTask
from script.task.classic.PostBountyTask import PostBountyTask
from script.task.classic.SittingObservingTask import SittingObservingTask
from script.task.classic.SwitchCharacterTask import SwitchCharacterTask
from script.task.classic.SwordTask import SwordTask
from script.task.classic.SwordThreeTask import SwordThreeTask
from script.task.classic.TeaStoryTask import TeaStoryTask
from script.task.classic.UrgentDeliveryTask import UrgentDeliveryTask
from script.task.classic.WorldShoutsTask import WorldShoutsTask


class TaskFactory:
    __instance = None

    def __init__(self):
        self.tasks = {}
        self.init()

    @staticmethod
    def instance():
        """
        获取TaskFactory的单例实例

        Returns:
            TaskFactory: 返回TaskFactory的单例实例
        """
        if TaskFactory.__instance is None:
            TaskFactory.__instance = TaskFactory()
        return TaskFactory.__instance

    def init(self):
        """
        初始化函数，用于注册课业任务类型

        参数:
            self: 类实例对象

        返回值:
            无
        """
        # 注册经典课业任务类型
        self.register("classic", "课业任务", LessonTask)
        self.register("classic", "帮派任务", FactionTask)
        self.register("classic", "门客设宴", DoorBanTask)
        self.register("classic", "破阵设宴", BreakBanTask)
        self.register("classic", "单人论剑", SwordTask)
        self.register("classic", "侠缘喊话", ChivalryShoutTask)
        self.register("classic", "每日兑换", DailyRedemptionTask)
        self.register("classic", "江湖急送", UrgentDeliveryTask)
        self.register("classic", "日常副本", DailyCopiesTask)
        self.register("classic", "世界喊话", WorldShoutsTask)
        self.register("classic", "每日一卦", HexagramDayTask)
        self.register("classic", "茶馆说书", TeaStoryTask)
        self.register("classic", "江湖行商", MerchantLakeTask)
        self.register("classic", "江湖英雄榜", HeroListTask)
        self.register("classic", "采集任务", AcquisitionTask)
        self.register("classic", "坐观万象", SittingObservingTask)
        self.register("classic", "发布悬赏", PostBountyTask)
        self.register("classic", "悬赏任务", BountyMissionsTask)
        self.register("classic", "多人论剑", SwordThreeTask)
        self.register("classic", "切换角色", SwitchCharacterTask)

    def register(self, model, name, task):
        """
        注册任务类型

        Args:
            model (str): 任务模型类型
            name (str): 任务名称
            task (class): 任务类
        """
        if model not in self.tasks:
            self.tasks[model] = {}
        self.tasks[model][name] = task

    def create(self, model, name):
        """
        创建任务实例

        Args:
            model (str): 任务模型类型
            name (str): 任务名称

        Returns:
            class: 返回对应的任务类，如果未找到则返回None
        """
        # 检查模型是否存在
        if model not in self.tasks:
            return None

        return self.tasks[model][name]
