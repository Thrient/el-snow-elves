from script.task.basis.classic.ClassicTask import ClassicTask


class LouLanDailyTask(ClassicTask):
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

            if self.timer.getElapsedTime() > 3600:
                self.logs("楼兰日常超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("楼兰日常完成")
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
                    from script.core.TaskFactory import TaskFactory
                    cls = TaskFactory.instance().create(self.taskConfig.model, "楼兰守护")
                    with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
                        obj.execute()
                    self.setup = 4
                case 4:
                    from script.core.TaskFactory import TaskFactory
                    cls = TaskFactory.instance().create(self.taskConfig.model, "楼兰采集")
                    with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
                        obj.execute()
                    self.setup = 0

        return None
