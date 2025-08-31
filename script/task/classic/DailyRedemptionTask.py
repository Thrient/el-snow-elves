from script.task.basis.ClassicTask import ClassicTask


class DailyRedemptionTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [True]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("每日兑换完成")
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
                    __event = not (self.taskConfig.silverNoteGiftBox or
                                   self.taskConfig.wuYueSwordBlank or
                                   self.taskConfig.baiGongDingBlank)

                    if __event and self.event[0]:
                        self.setup = 4
                        continue

                    self.event[0] = False

                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品珍宝阁")
                    self.touch("按钮珍宝阁绑元商城", y=-130)

                    if self.taskConfig.silverNoteGiftBox:
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input("银票礼盒")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁银票礼盒", box=(910, 170, 1190, 285)):
                            self.mouseClick((988, 694), count=30, timeout=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi()

                    if self.taskConfig.wuYueSwordBlank:
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input("吴越剑坯")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁吴越剑坯", box=(910, 170, 1190, 285)):
                            self.mouseClick((988, 694), count=5, timeout=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi(count=5)

                    if self.taskConfig.baiGongDingBlank:
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input("白公鼎坯")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁白公鼎坯", box=(910, 170, 1190, 285)):
                            self.mouseClick((988, 694), count=5, timeout=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi(count=2)

                    self.backToMain()
                    self.setup = 0
