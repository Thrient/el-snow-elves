from abc import ABC, abstractmethod

from script.config.Config import Config
from script.task.basis.BasisTask import BasisTask


class ClassicBasisTask(BasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def closeCurrentUi(self, count=1, box=Config.BOX):
        """关闭当前界面"""
        pass

    @abstractmethod
    def closeRewardUi(self, count=1):
        """关闭奖励"""
        pass

    @abstractmethod
    def backToMain(self):
        """返回主界面"""
        pass

    @abstractmethod
    def openBackpack(self):
        """打开包裹"""
        pass

    @abstractmethod
    def startInterconnected(self):
        """切换互联分线"""
        pass