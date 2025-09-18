import random
import time

from script.task.basis.ClassicTask import ClassicTask


class TeaStoryTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [False]

    def instance(self):
        return self

    def execute(self):
        while not self.finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("茶馆说书超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("茶馆说书完成")
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
                    self.verifyTouch("按钮活动江湖")

                    if self.touch("按钮活动摇钱树", y=45) is None:
                        self.logs("茶馆说书已经完成")
                        self.setup = 0
                        continue

                    self.arrive()
                    self.touch("按钮茶馆说书进入茶馆")
                    self.defer(5)
                    self.setup = 4
                case 4:
                    if self.exits("界面茶馆") is None:
                        self.setup = 3
                        continue

                    if self.exits("标志茶馆发布题目") is not None:
                        self.event[0] = True
                        continue

                    if self.exits("标志茶馆答题时间") is not None and self.event[0]:
                        self.logs("随机答题")
                        self.event[0] = False

                        actions = [
                            "按钮茶馆甲",
                            "按钮茶馆乙",
                            "按钮茶馆丙",
                            "按钮茶馆丁",
                        ]

                        # 随机选择并执行一个操作
                        self.touch(random.choice(actions))

                    if self.exits("按钮茶馆退出") is not None:
                        self.closeRewardUi(count=5)
                        self.touch("按钮茶馆退出")
                        self.setup = 0
                        continue
