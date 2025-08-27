import time

from script.task.basis.ClassicTask import ClassicTask


class DailyCopiesTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [time.time(), 1, 0, time.time()]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("帮派任务完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamCreate()
                    self.setup = 3
                case 3:
                    self.openTeam()
                    if len(self.exitsAll("标志队伍空位")) <= 10 - 1:
                        self.setup = 4
                        continue
                    self.touch("按钮队伍自动匹配_V1")

                    if time.time() - self.event[3] > 60:
                        self.event[3] = time.time()
                        self.worldShouts("sxy")
                case 4:
                    self.openTeam()
                    self.touch("按钮队伍进入副本")
                    self.touch("按钮确认")

                    self.waitMapLoading()
                    self.setup = 5

                case 5:
                    if time.time() - self.event[0] > 90:
                        self.event[0] = time.time()
                        if self.activatedTask("按钮任务副本", model="任务") is None:
                            self.event[1] += 1

                    if self.exits("按钮副本跳过剧情") is not None:
                        self.touch("按钮副本跳过剧情")

                    if self.exits("标志副本完成") is not None:
                        if self.event[2] > 4:
                            self.touch("按钮副本退出")
                            self.touch("按钮副本离开")
                            self.waitMapLoading()
                            self.setup = 0
                        self.event[2] += 1
