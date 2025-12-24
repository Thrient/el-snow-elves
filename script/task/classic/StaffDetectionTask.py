from script.task.basis.classic.ClassicTask import ClassicTask


class StaffDetectionTask(ClassicTask):
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
                self.logs("队员检测超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.backToMain()
                    self.logs("队员检测完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.instance()
                    # self.areaGo("金陵")
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "召唤队员"
                case "召唤队员":
                    self.openTeam()
                    if self.touch("按钮队伍一键召回"):
                        self.defer(count=20)
                    self.setup = "清理暂离队员"
                case "清理暂离队员":
                    self.openTeam()
                    if not self.touch("标志队伍暂离", y=45):
                        self.setup = "清理离线队员"
                        continue
                    self.touch("按钮队伍请离队伍")
                case "清理离线队员":
                    self.openTeam()
                    if not self.touch("标志队伍离线", y=45):
                        self.setup = "任务结束"
                        continue
                    self.touch("按钮队伍请离队伍")

        return None
