from script.task.basis.classic.ClassicTask import ClassicTask


class FactionPointsDanceTask(ClassicTask):
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
                self.logs("帮派积分跳舞超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.exitInstance()
                    self.logs("帮派积分跳舞完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.locationDetection()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "帮派领地"
                case "帮派领地":
                    self.openFaction()
                    self.touch("按钮帮派领地")
                    self.touch("按钮帮派前往领地")
                    self.arrive()
                    self.resetLens()
                    self.touch("按钮大世界共舞", "按钮大世界共舞_V1")
                    self.setup = "积分共舞"
                case "积分共舞":
                    if self.exits("标志共舞完成"):
                        self.touch("按钮取消")
                        self.setup = "任务结束"
                        continue
                    self.touch("按钮帮派积分共舞", pre_delay=250)

        return None
