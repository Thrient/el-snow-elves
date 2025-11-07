from script.task.basis.ClassicTask import ClassicTask


class BenefitCollectionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("福利领取超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("福利领取完成")
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
                    self.move_mouse(start=(1245, 630), end=(1245, 200))
                    self.touch("按钮物品福利")

                    self.setup = 4
                case 4:
                    self.touch("按钮福利江湖礼")
                    self.touch("按钮福利领取")
                    self.closeRewardUi(count=10)
                    self.keepAlive()
                    self.setup = 5

                case 5:
                    self.click_mouse(pos=(300, 640), count=2, post_delay=0.5)
                    self.click_mouse(pos=(400, 640), count=2, post_delay=0.5)
                    self.click_mouse(pos=(500, 640), count=2, post_delay=0.5)
                    self.click_mouse(pos=(600, 640), count=2, post_delay=0.5)
                    self.click_mouse(pos=(700, 640), count=2, post_delay=0.5)
                    self.closeRewardUi(count=10)
                    self.keepAlive()
                    self.setup = 6
                case 6:
                    self.click_mouse(pos=(450, 525))
                    self.click_mouse(pos=(170, 520))
                    self.closeRewardUi(count=10)
                    self.backToMain()
                    self.setup = 0


                    #
                    # self.touch("按钮特惠的标志拍照", x=-84, y=-642)
                    # self.touch("按钮周卡礼包")
                    # self.touch("按钮周卡每日领取的标志", x=-458)
                    # self.backToMain()
                    #
                    # self.openBackpack()
                    # self.touch("按钮物品综合入口")
                    # self.touch("按钮物品活动")
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.touch("标志活动活跃度", x=30, y=-30)
                    # self.backToMain()

                    pass

        return None
