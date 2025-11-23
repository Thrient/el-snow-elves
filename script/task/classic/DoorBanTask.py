from script.task.basis.ClassicTask import ClassicTask


class DoorBanTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件变量字典
        self.event = {
            "banquet_index": 1,  # 破阵设宴提交索引
            "banquet_counter": 0  # 破阵设宴提交次数计数器

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("门客设宴超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("门客设宴完成")
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
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动帮派")

                    if not self.touch("按钮活动门客设宴", y=45):
                        self.logs("门客设宴已经完成")
                        self.setup = 0
                        continue

                    self.touch("按钮活动前往邀约")
                    self.arrive()
                    self.touch("按钮门客设宴邀请赴宴")
                    self.touch("按钮门客设宴确认邀约")
                    self.setup = 4
                case 4:
                    if not self.exits("界面破阵设宴"):
                        self.setup = 3
                        continue

                    if self.event["banquet_index"] > 8:
                        self.setup = 6
                        continue

                    self.setup = 5
                case 5:
                    if self.event["banquet_counter"] > 9:
                        self.event["banquet_index"] += 1
                        self.event["banquet_counter"] = 0
                        self.setup = 4
                        continue

                    __x = (self.event["banquet_index"] - 1) % 4
                    __y = (self.event["banquet_index"] - 1) // 4

                    self.click_mouse(pos=(633 + 172 * __x, 282 + 182 * __y))

                    if not self.exits("按钮门客设宴获取"):
                        self.touch("按钮门客设宴一键提交")
                        self.event["banquet_index"] += 1
                        self.event["banquet_counter"] = 0
                        self.setup = 4
                        continue

                    self.click_mouse(pos=(0, 0))

                    self.touch("按钮门客设宴获取")

                    self.event["banquet_counter"] += 1

                    if self.event["banquet_counter"] in [1, 4, 6]:
                        if not self.exits("按钮帮派仓库"):
                            continue
                        self.touch("按钮帮派仓库", y=-75)
                        self.buy("帮派仓库")

                    elif self.event["banquet_counter"] in [2, 5, 7]:
                        if not self.exits("按钮摆摊购买"):
                            continue
                        self.touch("按钮摆摊购买", y=-75)
                        self.buy("摆摊购买")

                    elif self.event["banquet_counter"] in [3, 8, 9]:
                        if not self.exits("按钮商城购买"):
                            continue
                        self.touch("按钮商城购买", y=-75)
                        self.buy("商城购买")

                    self.setup = 4
                case 6:
                    if len(self.exits("标志门客设宴已提交", find_all=True)) >= 8:
                        self.touch("按钮门客设宴开始")
                        self.closeRewardUi(5)
                    self.setup = 0
        return None
