import time

from script.task.basis.ClassicTask import ClassicTask


class WorldShoutsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [time.time(), 1]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("世界喊话完成")
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
                    if time.time() - self.event[0] > 34:
                        self.event[0] = time.time()

                        self.WorldShoutsIndex = 0 \
                            if self.WorldShoutsIndex >= len(self.WorldShoutsTextList) + 1 \
                            else self.WorldShoutsIndex

                        self.backToMain()
                        self.keepAlive()
                        self.worldShouts(self.WorldShoutsTextList[self.WorldShoutsIndex],
                                         ordinary=self.taskConfig.ordinaryWorldShouts,
                                         connected=self.taskConfig.connectedWorldShouts)
                        self.WorldShoutsIndex += 1
                        self.logs(f"世界喊话 {self.event[1]} 次")
                        self.event[1] += 1

                    self.defer(1)
