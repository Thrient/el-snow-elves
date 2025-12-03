from script.task.basis.classic.ClassicTask import ClassicTask


class SittingObservingTask(ClassicTask):
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
                self.logs("坐观万象超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("坐观万象完成")
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

                    if not self.touch("按钮活动坐观万象", y=45):
                        self.logs("坐观万象已经完成")
                        self.setup = 0
                        continue

                    self.arrive()
                    self.setup = 4
                case 4:
                    if not self.exits("标志大世界修炼中"):
                        self.setup = 0
                        continue
                    self.defer(count=5)
                    self.keepAlive()
        return None
