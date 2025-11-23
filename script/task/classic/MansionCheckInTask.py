import random

from script.task.basis.ClassicTask import ClassicTask


class MansionCheckInTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "decline_counter": 0
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("宅邸打卡超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("宅邸打卡完成")
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
                    self.touch("按钮物品宅邸")
                    self.touch("按钮宅邸排行榜")
                    self.setup = 4
                case 4:
                    if not self.exits("界面排行榜"):
                        self.backToMain()
                        self.setup = 3
                        continue

                    if self.exits("标志宅邸打卡完成"):
                        self.backToMain()
                        self.setup = 0
                        continue

                    self.move_mouse(
                        start=(635, 670),
                        end=(635, 270),
                        count=random.randint(0, self.event["decline_counter"])
                    )
                    self.event["decline_counter"] += 1

                    self.touch("标志宅邸打卡经典")
                    if not self.touch("标志宅邸打卡参观"):
                        self.closeCurrentUi()
                        continue
                    self.backToMain(exclude_branches=["副本退出"])
                    self.setup = 5
                case 5:
                    self.defer(count=40)
                    self.closeRewardUi(count=5)
                    self.setup = 3


        return None
