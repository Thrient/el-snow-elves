from abc import ABC

from script.task.basis.classic.ClassicBasisTask import ClassicBasisTask


class ClassicBackpackTask(ClassicBasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def closeBackpack(self):
        """关闭背包"""
        if not self.exits("界面物品"):
            return
        self.logs("关闭背包")
        self.click_mouse(pos=(0, 0))
        self.closeCurrentUi()

    def openBackpack(self):
        """打开背包"""
        if self.exits("界面物品"):
            return
        self.logs("打开背包")
        self.click_key(key=self.taskConfig.keyList[20])
