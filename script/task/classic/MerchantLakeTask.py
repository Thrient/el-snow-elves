import time

from script.task.basis.ClassicTask import ClassicTask


class MerchantLakeTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.cache = None
        # 事件类型定义
        # 0: 江湖行商次数计数器
        # 1: 江湖行商喊话间隔计时器
        # 2: 江湖行商购买状态
        # 3: 江湖行商任务激活计时器
        self.event = [1, 0.0, True, 0.0]

    def instance(self):
        return self

    def resetEvent(self):

        if self.cache == self.setup:
            return
        self.cache = self.setup
        match self.cache:
            case 4:
                # 重置江湖行商喊话间隔计时器
                self.event[1] = 0.0
            case 6:
                # 重置江湖行商购买状态
                self.event[2] = True
                # 重置江湖行商任务激活计时器
                self.event[3] = time.time()

    def execute(self):
        while not self.finished.is_set():

            if 1800 * 2 * 6 < self.timer.getElapsedTime():
                self.logs("江湖行商超时")
                return 0

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
                    # 江湖行商剩余次数检测
                    if self.event[0] > self.taskConfig.merchantLakeCount:
                        self.setup = 0
                        continue

                    self.areaGo("江南", x=986, y=1190)
                    self.setup = 4
                case 4:
                    self.openTeam()

                    # 检查队伍人数
                    if len(self.exitsAll("标志队伍空位")) <= 10 - 3:
                        # 一键召回
                        self.followDetection()
                        self.setup = 5
                        continue
                    self.touch("按钮队伍自动匹配_V1", match=1)

                    # 世界喊话
                    if 34 < time.time() - self.event[1]:
                        self.event[1] = time.time()
                        self.worldShouts(self.taskConfig.merchantLakeWordShout, ordinary=True, connected=True)
                case 5:
                    # 对话行商NPC
                    self.touch("按钮大世界对话")
                    if self.touch("按钮江湖行商参与") is None:
                        self.setup = 3
                        continue

                    # 检测行商参与条件
                    if 3 != len(self.exitsAll("标志江湖行商参与条件")):
                        self.backToMain()
                        self.setup = 4
                        continue

                    self.touch("按钮江湖行商确认发起")
                    self.touch("按钮江湖行商货单购买")

                    # 等待全部队员准备
                    if self.wait("标志行商任务接取成功", overTime=20) is None:
                        self.backToMain()
                        self.setup = 4
                        continue
                    self.setup = 6
                case 6:

                    self.touch("按钮江湖行商威逼行商交易", y=85)

                    self.touch("按钮地图江南区域")

                    self.touch("按钮确定")

                    if 360 < time.time() - self.event[3]:
                        self.event[3] = time.time()
                        self.activatedTask("按钮任务副本", model="任务")
                        continue

                    if self.exits("按钮江湖行商一键上缴") is not None:
                        self.touch("按钮江湖行商一键上缴")
                        self.closeRewardUi(count=5)
                        self.logs(f"江湖行商完成{self.event[0]}次")
                        self.event[0] += 1
                        self.setup = 3
                        continue

                    if self.exits("界面行商") is not None:
                        # 行商购买
                        if self.event[2]:
                            self.mouseClick((1175, 170))
                            for pos in [(524, 258), (285, 258), (524, 178), (285, 178)]:
                                self.mouseClick(pos)
                                self.mouseClick((1037, 489), delay=3)
                                self.touch("按钮江湖行商购买")
                        # 行商出售
                        else:
                            self.mouseClick((1175, 270))
                            self.touch("按钮江湖行商出售", count=5)

                        self.event[2] = not self.event[2]
                        self.defer(count=5)
                        self.closeCurrentUi()

                    if self.exits("界面地图") is not None:
                        if self.exits("标志本体位置", "标志本体位置_V2") is not None:
                            if self.event[2]:
                                self.touch("标志本体位置", "标志本体位置_V2")
                            else:
                                self.touch("标志江湖行商商人", box=(1020, 150, 1125, 255))
                            continue

                        if self.exits("标志本体位置_V1") is not None:
                            if self.event[2]:
                                self.touch("标志本体位置_V1")
                            else:
                                self.touch("标志江湖行商商人", box=(960, 25, 1020, 110))
                            continue

