import time

from script.task.basis.ClassicTask import ClassicTask


class DailyCopiesTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [0, 1, 0, 0.0]

    def instance(self):
        return self

    def execute(self):
        while not self.finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("帮派任务超时")
                return 0

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
                    self.teamCreate(model="日常")
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
                    if 3 < self.event[1]:
                        self.teamDetection()
                        self.setup = 2
                        continue

                    if time.time() - self.event[0] > 300:
                        self.event[0] = time.time()
                        self.unstuck()
                        if self.activatedTask("按钮任务副本", model="任务") is None:
                            self.event[1] += 1
                        continue

                    if self.exits("按钮副本跳过剧情") is not None:
                        self.touch("按钮副本跳过剧情")

                    if self.exits("标志副本完成") is not None:
                        if self.event[2] > 4:
                            self.touch("按钮副本退出")
                            self.touch("按钮副本离开")
                            self.waitMapLoading()
                            self.setup = 0
                        self.event[2] += 1

                    self.keepAlive()
