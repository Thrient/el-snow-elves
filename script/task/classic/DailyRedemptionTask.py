from script.task.basis.ClassicTask import ClassicTask


class DailyRedemptionTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [True]

    def instance(self):
        return self

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("每日兑换超时")
                return 0

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

                    if "银票礼盒" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁绑元商城", y=-130)
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input(text="银票礼盒")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁银票礼盒", box=(910, 170, 1190, 285)):
                            self.click_mouse(pos=(988, 694), count=30, post_delay=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi()
                        self.backToMain()

                    if "吴越剑坯" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁绑元商城", y=-130)
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input(text="吴越剑坯")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁吴越剑坯", box=(910, 170, 1190, 285)):
                            self.click_mouse(pos=(988, 694), count=5, timeout=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi(5)
                        self.backToMain()

                    if "白公鼎坯" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁绑元商城", y=-130)
                        self.touch("按钮珍宝阁搜索")
                        self.touch("标志输入道具名称")
                        self.input(text="白公鼎坯")
                        self.touch("按钮珍宝阁搜索")
                        if self.exits("标志珍宝阁白公鼎坯", box=(910, 170, 1190, 285)):
                            self.click_mouse(pos=(988, 694), count=5, timeout=0.1)
                        self.touch("按钮珍宝阁搜索返回")
                        self.closeRewardUi(2)
                        self.backToMain()

                    self.setup = 4
                case 4:

                    if "商会鸡蛋" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁商会")

                        self.move_mouse(start=(186, 275), end=(186, 475), count=3)
                        self.touch("按钮珍宝阁宝石")
                        self.move_mouse(start=(186, 475), end=(186, 275))
                        self.touch("按钮珍宝阁江湖杂货")
                        self.move_mouse(start=(540, 275), end=(540, 475), count=3)
                        self.move_mouse(start=(540, 475), end=(540, 275))

                        self.touch("按钮珍宝阁一筐鸡蛋")
                        if self.exits("标志珍宝阁一筐鸡蛋", box=(750, 140, 1150, 270)):
                            self.click_mouse(pos=(945, 675), count=5, timeout=0.1)
                        self.closeRewardUi(5)
                        self.backToMain()

                    if "榫头卯眼" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁商会")

                        self.move_mouse(start=(186, 275), end=(186, 475), count=3)
                        self.touch("按钮珍宝阁宝石")
                        self.move_mouse(start=(186, 475), end=(186, 275))
                        self.touch("按钮珍宝阁江湖杂货")
                        self.move_mouse(start=(540, 275), end=(540, 475), count=3)
                        self.move_mouse(start=(540, 475), end=(540, 275), count=3)

                        self.touch("按钮珍宝阁榫头卯眼")
                        if self.exits("标志珍宝阁榫头卯眼", box=(750, 140, 1150, 270)):
                            self.click_mouse(pos=(945, 675), count=12, timeout=0.1)
                        self.closeRewardUi(12)
                        self.backToMain()

                    if "碧铜马坯" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品珍宝阁")
                        self.touch("按钮珍宝阁商会")

                        self.move_mouse(start=(186, 275), end=(186, 475), count=3)
                        self.touch("按钮珍宝阁宝石")
                        self.move_mouse(start=(186, 475), end=(186, 275), count=3)
                        self.touch("按钮珍宝阁古董材料")

                        self.touch("按钮珍宝阁碧铜马坯")
                        if self.exits("标志珍宝阁碧铜马坯", box=(750, 140, 1150, 270)):
                            self.click_mouse(pos=(945, 675), count=3, timeout=0.1)
                        self.closeRewardUi(12)
                        self.backToMain()

                    self.setup = 5
                case 5:
                    if "锦芳绣残片" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品积分")
                        self.touch("按钮物品社交")

                        self.touch("按钮物品桃李值", x=350)
                        if self.exits("标志兑换商店批量购买") is not None:
                            self.touch("按钮兑换商店批量购买")
                        self.touch("标志兑换商店输入名称搜索")
                        self.input(text="锦芳绣残片")
                        self.touch("按钮兑换商店搜索")

                        if self.exits("标志兑换商店锦芳绣残片", box=(750, 140, 1150, 270)):
                            self.touch("按钮满")
                            self.click_mouse(pos=(1015, 630))
                        self.backToMain()

                    self.setup = 6
                case 6:
                    if "帮派铜钱捐献" in self.taskConfig.dailyExchangeList:
                        self.openFaction()
                        self.touch("按钮帮派福利")
                        self.touch("按钮帮派捐献")
                        for _ in range(3):
                            self.click_mouse(pos=(285, 585), timeout=0.1)
                            self.touch("按钮确定")
                        self.backToMain()

                    if "帮派银两捐献" in self.taskConfig.dailyExchangeList:
                        self.openFaction()
                        self.touch("按钮帮派福利")
                        self.touch("按钮帮派捐献")
                        for _ in range(3):
                            self.click_mouse(pos=(660, 585), timeout=0.1)
                            self.touch("按钮确定")
                        self.backToMain()

                    self.setup = 7
                case 7:
                    if "莲子购买" in self.taskConfig.dailyExchangeList:
                        self.locationDetection()
                        self.areaGo("江南", x=670, y=1700)
                        self.touch("按钮大世界对话")
                        self.touch("按钮商人小蟹小虾")

                        if self.exits("标志兑换商店批量购买") is not None:
                            self.touch("按钮兑换商店批量购买")

                        if self.exits("标志杂货商人莲子", box=(750, 140, 1150, 270)):
                            self.touch("按钮满")
                            self.click_mouse(pos=(930, 630))
                        self.closeRewardUi()
                        self.backToMain()

                    if "艾草购买" in self.taskConfig.dailyExchangeList:
                        self.locationDetection()
                        self.areaGo("江南", x=673, y=1722)
                        self.touch("按钮大世界对话")
                        self.touch("按钮商人新鲜蔬菜")

                        if self.exits("标志兑换商店批量购买") is not None:
                            self.touch("按钮兑换商店批量购买")

                        if self.exits("标志杂货商人艾草", box=(750, 140, 1150, 270)):
                            self.touch("按钮满")
                            self.click_mouse(pos=(930, 630))
                        self.closeRewardUi()
                        self.backToMain()

                    self.setup = 8

                case 8:

                    if "神厨食材购买" in self.taskConfig.dailyExchangeList:
                        self.locationDetection()
                        self.areaGo("中原", x=1272, y=1725)
                        self.touch("按钮大世界对话")
                        self.touch("按钮商人购买食材")
                        if self.exits("标志兑换商店批量购买") is not None:
                            self.touch("按钮兑换商店批量购买")

                        for text in self.taskConfig.chefIngredientsTags:
                            self.touch("标志输入名称搜索")
                            self.input(text=text)
                            self.touch("按钮搜索")
                            self.touch("按钮满")
                            self.click_mouse(pos=(1015, 630))
                            self.touch("按钮搜索返回")
                        self.backToMain()

                    if "神厨调料购买" in self.taskConfig.dailyExchangeList:
                        self.locationDetection()
                        self.areaGo("中原", x=1272, y=1725)
                        self.touch("按钮大世界对话")
                        self.touch("按钮商人购买调料")
                        if self.exits("标志兑换商店批量购买") is not None:
                            self.touch("按钮兑换商店批量购买")

                        for text in self.taskConfig.chefSeasoningTags:
                            self.touch("标志输入名称搜索")
                            self.input(text=text)
                            self.touch("按钮搜索")
                            self.touch("按钮满")
                            self.click_mouse(pos=(1015, 630))

                            self.touch("按钮搜索返回")
                        self.backToMain()

                    self.setup = 9
                case 9:
                    if "发布悬赏" not in self.taskConfig.dailyExchangeList:
                        self.setup = 10
                        continue

                    from script.core.TaskFactory import TaskFactory
                    cls = TaskFactory.instance().create(self.taskConfig.model, "发布悬赏")

                    cls(hwnd=self.hwnd, window=self.window, win_console=self.win_console).instance().execute()

                    self.setup = 10

                case 10:
                    if "商票上缴" in self.taskConfig.dailyExchangeList:
                        self.openFaction()
                        self.touch("按钮帮派福利")
                        self.touch("按钮帮派商票上缴")
                        self.arrive()
                        self.touch("按钮行商商票上缴")

                        for _ in range(4):
                            self.touch("标志行商高级商票")
                            self.touch("按钮行商上缴")

                        self.backToMain()

                    self.setup = 11
                case 11:
                    if "摇钱树" in self.taskConfig.dailyExchangeList:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品活动")
                        self.touch("按钮活动帮派")

                        self.touch("按钮活动摇钱树", y=45)
                        self.touch("按钮摇钱树前往")
                        self.arrive()

                        self.touch(f"按钮摇钱树{self.taskConfig.moneyTreeSelect}")
                        self.closeRewardUi(5)
                        self.backToMain()

                    self.setup = 0
        return None
