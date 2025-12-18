from script.task.basis.classic.ClassicTask import ClassicTask


class BackInstanceTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
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
                case "任务结束":
                    self.logs("界面返回完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.locationDetection()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "关闭窗口"
                case "主界面判断":
                    if not self.exits("按钮世界挂机", times=5):
                        self.setup = "关闭窗口"
                        continue
                    self.setup = "任务结束"
                case "关闭窗口":
                    self.touch("按钮取消")
                    self.closeBackpack()
                    self.closeCurrentUi()
                    self.keepAlive()
                    self.setup = "主界面判断"

        return None
