from script.task.basis.classic.ClassicTask import ClassicTask


class BackInstanceTask(ClassicTask):
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
                self.logs("界面返回超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("界面返回完成")
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
                    if not self.exits("按钮世界挂机", times=5):
                        self.setup = 4
                        continue
                    self.setup = 0
                case 4:
                    self.closeBackpack()
                    self.closeCurrentUi()
                    self.keepAlive()
                    self.setup = 3

                    # if self.exits("标志购买确认"):
                    #     self.touch("按钮取消")
                    #
                    # if self.exits("按钮聊天退出"):
                    #     self.touch("按钮聊天退出")

        return None
