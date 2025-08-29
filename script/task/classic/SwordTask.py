from script.task.basis.ClassicTask import ClassicTask


class SwordTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [1]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("单人论剑完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    self.backToMain()
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动纷争")
                    self.touch("按钮活动华山论剑", x=-60, y=45)
                    self.setup = 4

                case 4:
                    if self.exits("界面单人论剑") is None:
                        if self.exits("标志单人论剑匹配成功") is not None:
                            self.logs(f"华山论剑第 {self.event[0]} 次")
                            self.event[0] += 1
                            self.waitMapLoading()
                            self.setup = 5
                            continue
                        self.setup = 3
                        continue

                    if self.exits("按钮单人论剑取消匹配") is None:
                        self.touch("按钮单人论剑匹配", match=1)

                    if self.exits("按钮确认") is not None:
                        self.touch("按钮确认", match=1)

                case 5:
                    self.keyClick("W", delay=3)

                    self.touch("按钮华山论剑准备")

                    self.setup = 6
                case 6:
                    if self.exits("标志单人论剑我方", "标志单人论剑敌方") is not None:
                        continue

                    self.touch("按钮华山论剑离开")

                    if self.event[0] > 10:
                        self.setup = 0
                        continue

                    self.waitMapLoading()
                    self.setup = 4
