from script.task.basis.classic.ClassicTask import ClassicTask


class EmailReceiveTask(ClassicTask):
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
                self.logs("邮件领取超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("邮件领取完成")
                    return 0
                # 位置检测
                case 1:
                    # self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    # self.teamDetection()
                    self.setup = 3
                case 3:
                    self.openFlyingEagle()
                    self.touch("按钮飞鹰一键领取", count=5)
                    self.closeRewardUi(count=20)
                    self.closeFlyingEagle()
                    self.setup = 0

        return None
