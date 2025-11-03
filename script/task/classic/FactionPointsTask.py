from script.task.basis.ClassicTask import ClassicTask


class FactionPointsTask(ClassicTask):
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
                self.logs("帮派积分超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("帮派积分完成")
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
                    self.openFaction()
                    self.touch("按钮帮派领地")
                    self.touch("按钮帮派前往领地")
                    self.arrive()
                    self.resetLens()
                    self.click_key(key="W", press_down_delay=0.2)
                    self.touch("按钮大世界清扫")

                    self.setup = 4
                case 4:
                    self.defer(count=12000)

                    self.setup = 0



        return None
