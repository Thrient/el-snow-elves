import time

from script.task.basis.ClassicTask import ClassicTask


class RedressingInjusticesTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "喊话计时器": 0.0,
            "任务激活计时器": 0.0
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            3: {"喊话计时器": 0.0},
            7: {"任务激活计时器": lambda: time.time()},
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("聚义平冤超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("聚义平冤完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamCreate(model="聚义平冤")
                    self.setup = 4
                case 3:
                    self.openTeam()

                    # 检查队伍人数
                    if len(self.exits("标志队伍空位", find_all=True)) <= 10 - 3:
                        # 一键召回
                        self.followDetection()
                        self.setup = 4
                        continue
                    self.touch("按钮队伍自动匹配")

                    # 世界喊话
                    if 34 < time.time() - self.event["喊话计时器"]:
                        self.event["喊话计时器"] = time.time()
                        self.worldShouts(self.taskConfig.merchantLakeWordShout, ordinary=True, connected=True)
                case 4:
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动行当")

                    if self.touch("按钮活动聚义平冤", y=45) is None:
                        self.setup = 0
                        continue

                    self.arrive()
                    self.setup = 5
                case 5:
                    if self.touch("按钮聚义平冤") is not None:
                        self.touch("按钮确定", post_delay=0)
                        self.setup = 6
                        continue
                    self.setup = 7
                case 6:
                    if self.wait("标志聚义任务接取成功", seconds=5) is None:
                        self.backToMain()
                        self.setup = 3
                        continue
                    self.setup = 7
                case 7:
                    if 360 < time.time() - self.event["任务激活计时器"]:
                        self.backToMain()
                        if self.activatedTask("按钮任务聚义", model="江湖") is not None:
                            self.event["任务激活计时器"] = time.time()
                        continue

                    if self.exits("标志聚义破门中", times=3) is not None:
                        self.defer(count=30)
                        self.setup = 0
                        continue

        return None
