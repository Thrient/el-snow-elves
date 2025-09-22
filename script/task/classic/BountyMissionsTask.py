import time

from script.task.basis.ClassicTask import ClassicTask


class BountyMissionsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.cache = None
        # 事件类型定义
        # 0: 副本喊话时间计数器
        # 1: 副本激活计时器
        # 2: 副本任务激活计数器
        # 3: 副本卡死计数器
        # 4: 副本退出判断计数器
        self.event = [0.0, 0.0, 0, 0, 0]

    def instance(self):
        return self

    def resetEvent(self):

        if self.cache == self.setup:
            return
        self.cache = self.setup
        match self.cache:
            case 5:
                # 重置副本喊话时间计数器
                self.event[0] = 0.0
            case 7:
                # 重置副本激活计时器
                self.event[1] = 0.0
                # 重置副本任务激活计数器
                self.event[2] = 0
                # 重置副本卡死计数器
                self.event[3] = 0
                # 重置副本退出判断计数器
                self.event[4] = 0

    def execute(self):
        while not self.finished.is_set():

            self.resetEvent()

            if 1800 * 2 * 6 < self.timer.getElapsedTime():
                self.logs("悬赏任务超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("悬赏任务完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamCreate(model="日常")
                    self.setup = 5
                case 3:
                    if self.exits("界面悬赏") is None:
                        self.verifyTouch("按钮活动悬赏")
                        self.touch("按钮悬赏下页", x=50)
                        continue

                    if self.exits("标志悬赏接满") is not None:
                        self.touch("按钮悬赏上页", x=-50)
                        self.setup = 4
                        continue
                    self.mouseClick((1100, 145), timeout=0.1)
                    if self.exits("标志悬赏江湖纪事", box=(265, 175, 1190, 565)) is None:
                        continue
                    self.touch("标志悬赏江湖纪事", y=325, timeout=0)
                    self.touch("按钮悬赏押金", timeout=0)
                case 4:
                    if self.exits("按钮悬赏前往") is None:
                        self.setup = 0
                        continue
                    self.backToMain()
                    self.setup = 5
                case 5:
                    self.openTeam()
                    if len(self.exitsAll("标志队伍空位")) <= 10 - 1:
                        self.setup = 6
                        continue
                    self.touch("按钮队伍自动匹配_V1")

                    if time.time() - self.event[0] > 32:
                        self.event[0] = time.time()
                        self.worldShouts("悬赏十连来人!!!")
                case 6:
                    self.openTeam()
                    self.touch("按钮队伍进入副本")
                    self.touch("按钮确认")

                    self.waitMapLoading()

                    self.setup = 7
                case 7:
                    if 3 < self.event[3]:
                        self.teamDetection()
                        self.setup = 2
                        continue

                    if 3 < self.event[2]:
                        self.event[2] = 0
                        self.event[3] += 1
                        self.unstuck()
                        continue

                    if 180 < time.time() - self.event[1]:
                        self.event[1] = time.time()
                        self.event[2] += 1
                        self.activatedTask("按钮任务副本", model="任务")
                        continue

                    if self.exits("按钮副本跳过剧情") is not None:
                        self.touch("按钮副本跳过剧情")

                    if self.exits("标志副本完成") is not None:
                        if 4 > self.event[4]:
                            self.event[4] += 1
                            continue
                        self.touch("按钮副本退出")
                        self.touch("按钮副本离开")
                        self.waitMapLoading()
                        self.setup = 3
                        continue
