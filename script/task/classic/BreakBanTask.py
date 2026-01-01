from script.task.basis.classic.ClassicTask import ClassicTask


class BreakBanTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件变量字典
        self.event = {
            "提交索引": 0,
            "获取次数计数器": 0,
            "提交标志": [False, False, False, False, False, False, False, False],

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            "提交道具": {"获取次数计数器": 0}
        }


    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("破阵设宴超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.backToMain()
                    self.logs("破阵设宴完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "前往设宴NPC"
                case "前往设宴NPC":
                    self.openActivity()
                    self.touch("按钮活动帮派")
                    if not self.touch("按钮活动破阵设宴", y=45):
                        self.setup = "任务结束"
                        continue
                    self.touch("按钮活动前往邀约")
                    self.arrive()
                    self.touch("按钮破阵设宴邀请赴宴")
                    self.touch("按钮破阵设宴确认邀约")
                    self.setup = "提交物品"
                case "提交物品":
                    self.event["提交索引"] += 1
                    self.logs(f"提交物品位置 {self.event["提交索引"]}")
                    __x = (self.event["提交索引"] - 1) % 4
                    __y = (self.event["提交索引"] - 1) // 4

                    self.click_mouse(pos=(633 + 172 * __x, 282 + 182 * __y))

                    self.setup = "获取道具"
                case "获取道具":
                    if not self.exits("按钮破阵设宴获取"):
                        self.setup = "提交道具"
                        continue

                    if self.event["获取次数计数器"] == 9:
                        self.setup = "提交道具"
                        continue

                    self.event["获取次数计数器"] += 1

                    self.touch("按钮破阵设宴获取")

                    if self.event["获取次数计数器"] in [1, 4, 6]:
                        if not self.exits("按钮帮派仓库"):
                            continue
                        self.touch("按钮帮派仓库", y=-75)
                        self.buy("帮派仓库")

                    elif self.event["获取次数计数器"] in [2, 5, 7]:
                        if not self.exits("按钮摆摊购买"):
                            continue
                        self.touch("按钮摆摊购买", y=-75)
                        self.buy("摆摊购买")

                    elif self.event["获取次数计数器"] in [3, 8, 9]:
                        if not self.exits("按钮商城购买"):
                            continue
                        self.touch("按钮商城购买", y=-75)
                        self.buy("商城购买")
                case "提交道具":
                    self.touch("按钮破阵设宴一键提交")
                    self.event["提交标志"][self.event["提交索引"] - 1] = True
                    self.setup = "开始设宴"
                case "开始设宴":
                    if self.event["提交索引"] < 8:
                        self.setup = "提交物品"
                        continue
                    if sum(self.event["提交标志"]) == 8:
                        self.touch("按钮破阵设宴开始")
                        self.closeRewardUi(5)
                    self.setup = "任务结束"
        return None
