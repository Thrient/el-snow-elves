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

    def staffDetection(self):
        """队员检测"""
        if self._finished.is_set():
            return
        from script.core.TaskFactory import TaskFactory

        cls = TaskFactory.instance().create(self.taskConfig.model, "队员检测")
        with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
            obj.execute()

    def teamCreate(self, model):
        """創建队伍"""
        self.logs(f"创建{model}队伍")

        def __team_1():
            self.logs("刷新当天日常")
            self.openBackpack()
            self.touch("按钮物品综合入口")
            self.touch("按钮物品活动")
            self.touch("按钮活动江湖")
            self.touch("按钮活动江湖纪事", y=45)
            self.backToMain()
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍江湖纪事")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        def __team_2():
            self.startInterconnected()
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍行当玩法")
            self.touch("按钮队伍江湖行商")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        def __team_3():
            self.startInterconnected()
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍行当玩法")
            self.touch("按钮队伍聚义平冤")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        _dict = {
            "日常": __team_1,
            "江湖行商": __team_2,
            "聚义平冤": __team_3
        }

        _dict[model]()
