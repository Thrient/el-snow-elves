from script.task.basis.ClassicTask import ClassicTask


class DouDiZhuTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "last_activated_time": 0.0,  # 上次激活任务时间
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
                    self.setup = 3
                case 3:
                    from script.core.TaskFactory import TaskFactory
                    cls = TaskFactory.instance().create(self.taskConfig.model, f"斗地主{self.taskConfig.douDiZhuMode}")
                    with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
                        obj.execute()
                    self.setup = 0
        return None
