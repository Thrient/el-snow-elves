from script.task.classic.AcquisitionTask import AcquisitionTask
from script.task.classic.ActivityRewardTask import ActivityRewardTask
from script.task.classic.AstrologyTask import AstrologyTask
from script.task.classic.BackInstanceTask import BackInstanceTask
from script.task.classic.BenefitCollectionTask import BenefitCollectionTask
from script.task.classic.BountyMissionsTask import BountyMissionsTask
from script.task.classic.BreakBanTask import BreakBanTask
from script.task.classic.ChefIngredientsTask import ChefIngredientsTask
from script.task.classic.ChivalryShoutTask import ChivalryShoutTask
from script.task.classic.DailyCopiesTask import DailyCopiesTask
from script.task.classic.DailyRedemptionTask import DailyRedemptionTask
from script.task.classic.DoorBanTask import DoorBanTask
from script.task.classic.DouDiZhuLoseTask import DouDiZhuLoseTask
from script.task.classic.DouDiZhuTask import DouDiZhuTask
from script.task.classic.DouDiZhuWinTask import DouDiZhuWinTask
from script.task.classic.EmailReceiveTask import EmailReceiveTask
from script.task.classic.ExchangeShopTask import ExchangeShopTask
from script.task.classic.FactionPointsDanceTask import FactionPointsDanceTask
from script.task.classic.FactionPointsTask import FactionPointsTask
from script.task.classic.FactionTask import FactionTask
from script.task.classic.HeroListTask import HeroListTask
from script.task.classic.HexagramDayTask import HexagramDayTask
from script.task.classic.LessonTask import LessonTask
from script.task.classic.LouLanCollectionTask import LouLanCollectionTask
from script.task.classic.LouLanDailyTask import LouLanDailyTask
from script.task.classic.LouLanGuardTask import LouLanGuardTask
from script.task.classic.MansionCheckInTask import MansionCheckInTask
from script.task.classic.MerchantLakeTask import MerchantLakeTask
from script.task.classic.PostBountyTask import PostBountyTask
from script.task.classic.RedressingInjusticesTask import RedressingInjusticesTask
from script.task.classic.RewardsClaimTask import RewardsClaimTask
from script.task.classic.RiverTask import RiverTask
from script.task.classic.SectTrialsDailyTask import SectTrialsDailyTask
from script.task.classic.SittingObservingTask import SittingObservingTask
from script.task.classic.SkyCurtainElegantGardenTask import SkyCurtainElegantGardenTask
from script.task.classic.SwitchCharacterTask import SwitchCharacterTask
from script.task.classic.SwordTask import SwordTask
from script.task.classic.SwordThreeTask import SwordThreeTask
from script.task.classic.TeaStoryTask import TeaStoryTask
from script.task.classic.UniqueSkillsTask import UniqueSkillsTask
from script.task.classic.UrgentDeliveryTask import UrgentDeliveryTask
from script.task.classic.VientianeLikesTask import VientianeLikesTask
from script.task.classic.WeekDailyPack import WeekDailyPack
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
        self.register("classic", "山河器", RiverTask)
        self.register("classic", "帮派积分", FactionPointsTask)
        self.register("classic", "行当绝活", UniqueSkillsTask)
        self.register("classic", "万象刷赞", VientianeLikesTask)
        self.register("classic", "天幕雅苑", SkyCurtainElegantGardenTask)
        self.register("classic", "邮件领取", EmailReceiveTask)
        self.register("classic", "神厨食材", ChefIngredientsTask)
        self.register("classic", "兑换商店", ExchangeShopTask)
        self.register("classic", "紫薇斗数", AstrologyTask)
        self.register("classic", "福利领取", BenefitCollectionTask)
        self.register("classic", "宗门试炼日常", SectTrialsDailyTask)
        self.register("classic", "宅邸打卡", MansionCheckInTask)
        self.register("classic", "活跃度奖励", ActivityRewardTask)
        self.register("classic", "周卡每日礼包", WeekDailyPack)
        self.register("classic", "楼兰日常", LouLanDailyTask)
        self.register("classic", "楼兰守护", LouLanGuardTask)
        self.register("classic", "楼兰采集", LouLanCollectionTask)
        self.register("classic", "聚义平冤", RedressingInjusticesTask)
        self.register("classic", "奖励招领", RewardsClaimTask)
        self.register("classic", "斗地主赢", DouDiZhuWinTask)
        self.register("classic", "斗地主输", DouDiZhuLoseTask)
        self.register("classic", "斗地主", DouDiZhuTask)
        self.register("classic", "界面返回", BackInstanceTask)
        self.register("classic", "帮派积分跳舞", FactionPointsDanceTask)
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
