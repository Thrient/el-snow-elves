from abc import ABC

from script.task.basis.classic.ClassicBasisTask import ClassicBasisTask


class ClassicTeamTask(ClassicBasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def closeTeam(self):
        """关闭队伍"""
        if not self.exits("界面队伍"):
            return
        self.logs("关闭队伍")
        self.closeCurrentUi()

    def openTeam(self):
        """打开队伍"""
        if self.exits("界面队伍"):
            return
        self.logs("打开队伍")
        self.click_key(key=self.taskConfig.keyList[22])
