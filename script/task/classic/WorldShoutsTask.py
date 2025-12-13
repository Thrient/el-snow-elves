import time

from script.task.basis.classic.ClassicTask import ClassicTask


class WorldShoutsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "shout_timer": 0.0,  # 喊话计时器
            "shout_counter": 0,  # 喊话次数计数器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 3:
                self.logs("世界喊话超时")
                return 0

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
                    if self.event["shout_counter"] > self.taskConfig.worldShoutsCount:
                        self.setup = 0
                        continue

                    if time.time() - self.event["shout_timer"] > 34:
                        self.event["shout_timer"] = time.time()

                        self.WorldShoutsIndex = 0 \
                            if self.WorldShoutsIndex >= len(self.WorldShoutsTextList) \
                            else self.WorldShoutsIndex

                        self.keepAlive()
                        self.worldShouts(self.WorldShoutsTextList[self.WorldShoutsIndex],
                                         ordinary=self.taskConfig.ordinaryWorldShouts,
                                         connected=self.taskConfig.connectedWorldShouts)
                        self.WorldShoutsIndex += 1
                        self.logs(f"世界喊话 {self.event["shout_counter"]} 次")
                        self.event["shout_counter"] += 1

                    self.defer(1)
        return None
