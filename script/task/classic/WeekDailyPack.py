from script.task.basis.ClassicTask import ClassicTask


class WeekDailyPack(ClassicTask):
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
                self.logs("周卡每日礼包超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("周卡每日礼包完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 4
                case 3:
                    self.backToMain()
                    self.touch("按钮大世界展开")
                    self.setup = 4

                case 4:
                    if not self.touch("按钮大世界特惠"):
                        self.setup = 3
                        continue
                    self.setup = 5
                case 5:
                    if not self.exits("界面特惠"):
                        self.setup = 4
                        continue

                    self.touch("按钮特惠周卡")
                    self.click_mouse(pos=(130, 695))
                    self.setup = 0

        return None
