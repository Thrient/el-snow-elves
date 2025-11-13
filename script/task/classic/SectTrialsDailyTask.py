from script.task.basis.ClassicTask import ClassicTask


class SectTrialsDailyTask(ClassicTask):
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
                self.logs("宗门试炼日常超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("宗门试炼日常完成")
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
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品天下宗师")
                    self.setup = 4
                case 4:
                    if self.exits("界面天下宗师") is None:
                        self.backToMain()
                        self.setup = 3
                        continue

                    self.touch("按钮天下宗师宗门玩法")
                    self.touch("按钮天下宗师宗门试炼")
                    self.setup = 5
                case 5:
                    if self.exits("界面宗门试炼") is None:
                        self.backToMain()
                        self.setup = 4
                        continue

                    _coord = self.exits("标志宗门试炼进度")

                    if _coord is None:
                        self.backToMain()
                        self.setup = 4
                        continue

                    self.move_mouse(start=(_coord[0], _coord[1]), end=(402, 560))

                    self.touch("按钮宗门试炼挑战")
                    self.touch("标志宗门试炼队伍一")
                    self.touch("按钮确认")
                    self.setup = 6
                case 6:
                    self.touch("标志继续", "按钮返回", seconds=60)
                    self.touch("标志继续", seconds=None)
                    self.backToMain()
                    self.setup = 0

        return None
