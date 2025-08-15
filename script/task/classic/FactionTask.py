import time

from script.task.basis.ClassisTask import ClassicTask


class FactionTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [time.time()]

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("课业任务完成")
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
                    self.touch("按钮活动帮派")
                    if self.touch("按钮活动止杀", y=45) is None:
                        self.logs("课业任务已经完成")
                        self.setup = 0
                        continue
