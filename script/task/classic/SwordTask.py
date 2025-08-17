import time

from script.task.basis.ClassicTask import ClassicTask


class SwordTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [0, 1]

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
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
                        self.setup = 5
                        continue

                    if self.exits("按钮单人论剑取消匹配") is None:
                        self.touch("按钮单人论剑匹配")

                    self.touch("按钮确认", match=1)
                case 5:
                    if self.event[0] > 3:
                        self.setup = 3
                        self.event[0] = 0
                        continue

                    if self.exits("标志地图加载", "标志地图加载_1") is not None:
                        continue

                    if self.exits("标志单人论剑匹配成功") is not None:
                        continue

                    self.event[0] += 1

                    if self.exits("标志单人论剑我方", "标志单人论剑敌方") is None:
                        continue

                    self.setup = 6
                    self.event[0] = 0
                case 6:
                    self.logs(f"华山论剑第 {self.event[1]} 次")

                    self.event[1] += 1

                    self.keyClick("W", delay=3)

                    self.touch("按钮华山论剑准备")

                    self.setup = 7
                case 7:
                    if self.exits("标志单人论剑我方", "标志单人论剑敌方") is None:
                        continue

                    self.touch("按钮华山论剑离开")
                    if self.event[1] > 2:
                        self.setup = 0
                        continue
                    self.waitMapLoading()
                    self.event[0] += 1
                    self.setup = 4
