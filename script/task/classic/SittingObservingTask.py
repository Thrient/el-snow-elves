import time

from script.task.basis.ClassicTask import ClassicTask


class SittingObservingTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [time.time() - 60]

    def instance(self):
        return self

    def execute(self):
        while not self.finished.is_set():

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
                    self.verifyTouch("按钮活动游历")

                    if self.touch("按钮活动坐观万象", y=45) is None:
                        self.logs("坐观万象已经完成")
                        self.setup = 0
                        continue

                    self.arrive()
                    self.setup = 4
                case 4:
                    if self.exits("标志大世界修炼中") is None:
                        self.setup = 0
                        continue
                    self.defer(5)
