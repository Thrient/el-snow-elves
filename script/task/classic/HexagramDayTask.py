from script.task.basis.classic.ClassicTask import ClassicTask


class HexagramDayTask(ClassicTask):
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
                self.logs("每日一卦超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("每日一卦完成")
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
                    self.touch("按钮活动游历")

                    if not self.touch("按钮活动每日一挂", y=45):
                        self.logs("每日一卦已经完成")
                        self.setup = 0
                        continue

                    self.arrive()
                    self.touch("按钮每日一卦算命占卜")
                    self.touch("按钮每日一卦确定")
                    self.setup = 4
                case 4:
                    if not self.exits("界面每日一卦"):
                        self.setup = 3
                        continue

                    self.touch("按钮每日一卦听天由命")
                    self.touch("按钮每日一卦占卜")
                    self.defer(4)
                    self.touch("按钮每日一卦接受卦象")
                    self.touch("按钮确定")
                    self.closeRewardUi(count=5)

                    self.setup = 0
        return None
