from script.task.basis.ClassicTask import ClassicTask


class SwordThreeTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.cache = None
        # 事件类型定义
        # 0: 多人论剑次数计数器
        # 1: 多人论剑战斗状态标志
        self.event = [1, False]

    def instance(self):
        return self

    def resetEvent(self):

        if self.cache == self.setup:
            return
        self.cache = self.setup
        match self.cache:
            case 5:
                # 重置单人论剑战斗状态标志
                self.event[1] = False

    def execute(self):
        while not self.finished.is_set():

            self.resetEvent()

            if self.timer.getElapsedTime() > 1800 * 2 * 3:
                self.logs("多人论剑超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("多人论剑完成")
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
                    self.verifyTouch("按钮活动纷争")

                    self.touch("按钮活动华山论剑", "按钮活动萌芽论剑", x=50, y=45)

                    self.setup = 4
                case 4:
                    # 检测多人论剑次数
                    if self.taskConfig.swordFightCount < self.event[0]:
                        self.setup = 0
                        continue

                    if self.exits("按钮单人论剑取消匹配") is None:
                        self.touch("按钮单人论剑匹配")

                    # 界面检测
                    if self.exits("界面多人论剑") is not None:
                        continue

                    # 匹配成功标志检测
                    if self.exits("标志多人论剑匹配成功") is None:
                        self.setup = 3
                        continue

                    self.logs(f"华山论剑第 {self.event[0]} 次")
                    self.event[0] += 1
                    self.defer(5)
                    self.waitMapLoading()
                    self.setup = 5

                case 5:

                    if self.exits("标志多人论剑我方", "标志多人论剑敌方") is None:
                        self.setup = 6
                        continue

                    if self.exits("标志多人论剑准备剩余时间") is not None:
                        self.touch("按钮华山论剑准备", overTime=0.1)
                        continue

                    if self.exits("标志多人论剑战斗剩余时间") is None:
                        continue

                    if self.event[1]:
                        continue
                    self.event[1] = True

                    self.keyClick("W", delay=3)
                    self.autoFightStart()

                case 6:
                    self.touch("按钮华山论剑离开")
                    # 停止自动战斗模式
                    self.autoFightStop()
                    # 等待地图加载完成
                    self.waitMapLoading()
                    self.setup = 4
















