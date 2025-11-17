from script.task.basis.ClassicTask import ClassicTask


class ActivityRewardTask(ClassicTask):
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
                self.logs("活跃度奖励超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("活跃度奖励完成")
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

                    self.setup = 4
                case 4:
                    if self.exits("界面活动") is None:
                        self.setup = 3
                        continue
                    self.click_mouse(pos=(1270, 700), count=8)
                    self.closeRewardUi(count=15)
                    self.setup = 0

        return None
