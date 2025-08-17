from script.task.basis.ClassicTask import ClassicTask


class DoorBanTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [1, 0]

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
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
                    self.backToMain()
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动帮派")
                    if self.touch("按钮活动门客设宴", y=45) is None:
                        self.logs("门客设宴已经完成")
                        self.setup = 0
                        continue

                    self.touch("按钮活动前往邀约")
                    self.arrive()
                    self.touch("按钮门客设宴邀请赴宴")
                    self.touch("按钮门客设宴确认邀约")
                    self.setup = 4
                case 4:
                    if self.exits("界面门客设宴") is None:
                        self.setup = 3
                        continue

                    if self.event[0] > 9:
                        self.setup = 5
                        continue

                    if self.event[1] > 9:
                        self.event[0] += 1
                        self.event[1] = 0
                        continue

                    __x = (self.event[0] - 1) % 4
                    __y = (self.event[0] - 1) // 4

                    self.mouseClick((633 + 172 * __x, 282 + 182 * __y))

                    if self.exits("按钮门客设宴获取") is None:
                        self.touch("按钮门客设宴一键提交")
                        self.event[0] += 1
                        self.event[1] = 0
                        continue

                    self.mouseClick((0, 0))

                    self.touch("按钮门客设宴获取")

                    self.event[1] += 1

                    if self.event[1] in [1, 4, 6]:
                        if self.exits("按钮帮派仓库") is None:
                            continue
                        self.touch("按钮帮派仓库", y=-75)
                        self.buy("帮派仓库")

                    elif self.event[1] in [2, 5, 7]:
                        if self.exits("按钮摆摊购买") is None:
                            continue
                        self.touch("按钮摆摊购买", y=-75)
                        self.buy("摆摊购买")

                    elif self.event[1] in [3, 8, 9]:
                        if self.exits("按钮商城购买") is None:
                            continue
                        self.touch("按钮商城购买", y=-75)
                        self.buy("商城购买")

                case 5:
                    if len(self.exitsAll("标志门客设宴已提交")) >= 8:
                        self.touch("按钮门客设宴开始")
                    self.closeRewardUi(5)
                    self.backToMain()
                    self.setup = 0
