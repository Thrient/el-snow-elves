import time

from script.task.basis.ClassicTask import ClassicTask


class MerchantLakeTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [time.time(), 0, (580, 355, 725, 480), (1020, 150, 1125, 255), False, (), (960, 25, 1020, 110)]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("江湖行商完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamCreate(model="江湖行商")
                    self.setup = 3
                case 3:
                    self.areaGo("江南", x=986, y=1190)
                    self.setup = 4
                case 4:
                    self.openTeam()

                    if len(self.exitsAll("标志队伍空位")) <= 10 - 3:
                        self.closeTeam()
                        self.setup = 5
                        continue
                    self.touch("按钮队伍自动匹配_V1")
                case 5:
                    self.touch("按钮大世界对话")
                    self.touch("按钮江湖行商参与")
                    self.touch("按钮江湖行商确认发起")
                    self.touch("按钮江湖行商货单购买")
                    self.defer(25)
                    self.setup = 6
                case 6:
                    if self.event[1] > 3:
                        self.logs("任务激活失败三次")
                        self.teamDetection()
                        self.setup = 2
                        continue

                    if time.time() - self.event[0] > 120:
                        self.event[0] = time.time()
                        if self.activatedTask("按钮任务行商", model="江湖") is None and self.event[1] < 3:
                            self.event[1] += 1
                            continue
                        self.event[1] = 0
                        continue

                    if self.exits("按钮江湖行商一键上缴") is not None:
                        self.touch("按钮江湖行商一键上缴")
                        self.closeRewardUi(5)
                        self.setup = 0
                        continue

                    if self.exits("按钮地图江南区域") is not None:
                        self.touch("按钮地图江南区域")
                        self.defer(3)

                        if self.exits("标志本体位置") is not None:
                            if self.event[4]:
                                self.event[5] = self.event[3]
                            else:
                                self.event[5] = self.event[2]

                        elif self.exits("标志本体位置_V1") is not None:
                            if self.event[4]:
                                self.event[5] = self.event[7]
                            else:
                                self.event[5] = self.event[3]
                        elif self.exits("标志本体位置_V2") is not None:
                            if self.event[4]:
                                self.event[5] = self.event[3]
                            else:
                                self.event[5] = self.event[7]

                        self.touch("标志本体位置", "标志本体位置_V1", "标志本体位置_V2", "标志江湖行商商人",
                                   box=self.event[5])
                        self.touch("按钮确定")
                        continue

                    if self.exits("按钮江湖行商威逼行商交易") is not None and not self.event[4]:
                        self.touch("按钮江湖行商威逼行商交易", y=85)
                        for pos in [(524, 258), (285, 258), (524, 178), (285, 178)]:
                            self.mouseClick(pos)
                            self.mouseClick((1037, 489), delay=3)
                            self.touch("按钮江湖行商购买")

                        self.event[4] = True
                        self.defer(count=5)
                        self.closeCurrentUi()

                        continue

                    if self.exits("按钮江湖行商威逼行商交易") is not None and self.event[4]:
                        self.touch("按钮江湖行商威逼行商交易", y=85)
                        self.touch("按钮江湖行商出售", count=5)
                        self.event[4] = False
                        self.defer(count=5)
                        self.closeCurrentUi()
                        continue
