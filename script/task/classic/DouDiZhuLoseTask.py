from script.task.basis.ClassicTask import ClassicTask


class DouDiZhuLoseTask(ClassicTask):
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
                self.logs("课业任务超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("课业任务完成")
                    return 0
                # 位置检测
                case 1:
                    # self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    # self.teamDetection()
                    self.setup = 4
                case 3:
                    if self.touch("按钮大世界上桌") is None:
                        self.setup = 0
                        continue
                    self.setup = 4
                case 4:
                    if self.exits("界面斗地主") is None:
                        self.backToMain(exclude_branches=["副本退出"])
                        self.setup = 3
                        continue

                    if self.exits("按钮斗地主准备") is not None:
                        self.touch("按钮斗地主准备")

                    if self.exits("按钮斗地主不叫", "按钮斗地主不抢", "按钮斗地主不加倍") is not None:
                        self.touch("按钮斗地主不叫", "按钮斗地主不抢", "按钮斗地主不加倍")

                    if self.exits("按钮斗地主不出", "按钮斗地主要不起") is not None:
                        self.touch("按钮斗地主不出", "按钮斗地主要不起")

        return None
