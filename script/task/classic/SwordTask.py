import time

from script.task.basis.ClassicTask import ClassicTask


class SwordTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [1]

    def instance(self):
        return self

    def execute(self):
        while not self.finished.is_set():

            if time.time() - self.timer.getElapsedTime() > 1800 * 2 * 3:
                self.logs("单人论剑超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("单人论剑完成")
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
                    self.executionActivities("单人论剑")
                    self.setup = 4
                case 4:
                    if self.taskConfig.swordFightCount < self.event[0]:
                        self.setup = 0
                        continue

                    if self.exits("界面单人论剑") is None:
                        if self.exits("标志单人论剑匹配成功") is not None:
                            self.logs(f"华山论剑第 {self.event[0]} 次")
                            self.event[0] += 1
                            self.defer(3)
                            self.waitMapLoading()
                            self.setup = 5
                            continue
                        self.setup = 3
                        continue

                    if self.exits("按钮单人论剑取消匹配") is None:
                        self.touch("按钮单人论剑匹配", match=1)

                    if self.exits("按钮确认") is not None:
                        self.touch("按钮确认", match=1)

                case 5:
                    # 检查是否处于论剑场景
                    if self.exits("标志单人论剑我方", "标志单人论剑敌方") is None:
                        self.leavingSwordFight()
                        self.setup = 4
                        continue

                    # 判断是否主动退出
                    if self.taskConfig.swordFightInitiativeExit:
                        self.touch("按钮副本退出")
                        self.touch("按钮确定")
                        self.waitMapLoading()
                        self.setup = 4
                        continue

                    if self.exits("标志单人论剑准备剩余时间") is not None:
                        self.touch("按钮华山论剑准备")

                    if self.exits("标志单人论剑战斗剩余时间") is not None:
                        self.keyClick("W", delay=3)
                        self.autoFightStart()
                        self.setup = 6
                case 6:
                    # 检查是否处于论剑场景
                    if self.exits("标志单人论剑我方", "标志单人论剑敌方") is None:
                        self.leavingSwordFight()
                        self.setup = 4
                        continue

    def leavingSwordFight(self):
        """
        离开华山论剑战斗场景

        该函数执行离开华山论剑战斗的完整流程，包括点击离开按钮、
        停止自动战斗和等待地图加载完成

        参数:
            无

        返回值:
            无
        """
        # 点击华山论剑离开按钮
        self.touch("按钮华山论剑离开")
        # 停止自动战斗模式
        self.autoFightStop()
        # 等待地图加载完成
        self.waitMapLoading()
