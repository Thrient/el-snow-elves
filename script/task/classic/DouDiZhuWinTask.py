from script.task.basis.classic.ClassicTask import ClassicTask


class DouDiZhuWinTask(ClassicTask):
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
                self.logs("课业任务超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("课业任务完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.locationDetection()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "准备上桌"
                case "准备上桌":
                    if not self.touch("按钮大世界上桌"):
                        self.setup = "任务结束"
                        continue
                    self.setup = "斗地主中"
                case "斗地主中":
                    if self.exits("按钮斗地主准备"):
                        self.touch("按钮斗地主准备")

                    if self.exits("按钮斗地主叫地主", "按钮斗地主抢地主", "按钮斗地主不加倍"):
                        self.touch("按钮斗地主叫地主", "按钮斗地主抢地主", "按钮斗地主不加倍")

                    if self.exits("按钮斗地主提示", "按钮斗地主出牌"):
                        self.touch("按钮斗地主提示", post_delay=0)
                        self.touch("按钮斗地主出牌", post_delay=0)

        return None
