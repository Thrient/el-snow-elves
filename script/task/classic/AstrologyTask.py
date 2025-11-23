from script.task.basis.ClassicTask import ClassicTask


class AstrologyTask(ClassicTask):
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
                self.logs("紫薇斗数超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("紫薇斗数完成")
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
                    self.touch("按钮物品紫薇斗数")
                    self.setup = 4
                case 4:
                    if not self.exits("界面紫薇斗数"):
                        self.backToMain()
                        self.setup = 3
                        continue
                    self.touch("按钮紫薇斗数推演")
                    self.touch("按钮紫薇斗数培养一次", count=2, post_delay=0.5)
                    self.backToMain()
                    self.setup = 0

        return None
