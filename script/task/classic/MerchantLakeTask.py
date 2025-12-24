import random
import time

from script.task.basis.classic.ClassicTask import ClassicTask


class MerchantLakeTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件变量字典
        self.event = {
            "行商次数计数器": 1,
            "喊话计时器": 0.0,
            "购买状态": True,
            "任务激活计时器": 0.0,
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            "接取行商任务": {
                "购买状态": True,
                "任务激活计时器": 0
            }
        }

    def execute(self):
        while not self._finished.is_set():

            if 1800 * 2 * 6 < self.timer.getElapsedTime():
                self.logs("江湖行商超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("江湖行商完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.instance()
                    self.areaGo("江南")
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamCreate(model="江湖行商")
                    self.setup = "行商次数检测"
                case "行商次数检测":
                    # 江湖行商剩余次数检测
                    if self.event["行商次数计数器"] > self.taskConfig.merchantLakeCount:
                        self.setup = "任务结束"
                        continue
                    self.setup = "前往行商NPC"
                case "前往行商NPC":
                    self.coordGo(x=986, y=1190)
                    self.setup = "接取行商任务"
                case "队伍人数检测":
                    self.openTeam()

                    # 检查队伍人数
                    if len(self.exits("标志队伍空位", find_all=True)) <= 10 - 3:
                        self.staffDetection()
                        self.setup = "接取行商任务"
                        continue

                    if 34 < time.time() - self.event["喊话计时器"]:
                        self.event["喊话计时器"] = time.time()
                        self.setup = "行商队员喊话"
                        continue

                    self.touch("按钮队伍自动匹配")
                case "行商队员喊话":
                    self.worldShouts(self.taskConfig.merchantLakeWordShout, ordinary=True, connected=True)
                    self.setup = "队伍人数检测"
                case "换线中":
                    self.backToMain()
                    self.switchBranchLine(random.randint(1, 10))
                    self.setup = "前往行商NPC"
                case "接取行商任务":
                    # 对话行商NPC
                    self.touch("按钮大世界对话")
                    if not self.touch("按钮江湖行商参与"):
                        self.setup = "换线中"
                        continue

                    # 检测行商参与条件
                    if 3 != len(self.exits("标志江湖行商参与条件", find_all=True)):
                        self.backToMain()
                        self.setup = "队伍人数检测"
                        continue

                    self.touch("按钮江湖行商确认发起")
                    self.touch("按钮江湖行商货单购买")

                    # 等待全部队员准备
                    if self.wait("标志行商任务次数耗尽", seconds=5):
                        self.backToMain()
                        self.setup = "任务结束"
                        continue
                    self.defer(count=20)
                    self.setup = "等待任务完成"
                case "任务检测":
                    if not self.activatedTask("按钮任务行商", model="江湖"):
                        self.setup = "行商次数检测"
                        continue
                    self.setup = "等待任务完成"
                case "等待任务完成":

                    if 720 < time.time() - self.event["任务激活计时器"]:
                        self.event["任务激活计时器"] = time.time()
                        self.setup = "任务检测"
                        continue

                    if self.exits("按钮江湖行商一键上缴"):
                        self.setup = "任务完成"
                        continue

                    self.touch("按钮江湖行商威逼行商交易", y=85)

                    self.touch("按钮地图江南区域")

                    self.touch("按钮确定")

                    if self.exits("界面行商"):
                        # 行商购买
                        if self.event["购买状态"]:
                            self.click_mouse(pos=(1175, 170))
                            for pos in [(524, 258), (285, 258), (524, 178), (285, 178)]:
                                self.click_mouse(pos=pos)
                                self.click_mouse(pos=(1037, 489), press_down_delay=3)
                                self.touch("按钮江湖行商购买")
                        # 行商出售
                        else:
                            self.click_mouse(pos=(1175, 270))
                            self.touch("按钮江湖行商出售", count=5)

                        self.event["购买状态"] = not self.event["购买状态"]
                        self.defer(count=5)
                        self.closeCurrentUi()

                    if self.exits("界面地图"):
                        if self.exits("标志本体位置", "标志本体位置_V2"):
                            if self.event["购买状态"]:
                                self.touch("标志本体位置", "标志本体位置_V2")
                            else:
                                self.touch("标志江湖行商商人", box=(1020, 150, 1125, 255))
                            continue

                        if self.exits("标志本体位置_V1"):
                            if self.event["购买状态"]:
                                self.touch("标志本体位置_V1")
                            else:
                                self.touch("标志江湖行商商人", box=(960, 25, 1020, 110))
                            continue
                        self.touch("标志江湖行商商人", box=(960, 25, 1125, 255))
                case "任务完成":
                    self.touch("按钮江湖行商一键上缴")
                    self.closeRewardUi(count=10)
                    self.logs(f"江湖行商完成{self.event["行商次数计数器"]}次")
                    self.event["行商次数计数器"] += 1
                    self.setup = "行商次数检测"

        return None
