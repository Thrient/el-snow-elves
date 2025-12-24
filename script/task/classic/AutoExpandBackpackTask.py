from script.task.basis.classic.ClassicTask import ClassicTask


class AutoExpandBackpackTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件类型定义
        self.event = {
            "解锁背包次数": 1

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("扩展背包超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    # self.exitInstance()
                    self.logs("扩展背包完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "打开拍照界面"
                case "滑动背包":
                    self.openBackpack()
                    self.move_mouse(start=(960, 610), end=(960, 310), count=3)
                case "检测背包格子":
                    if self.event["解锁背包次数"] > 5:
                        self.setup = "任务结束"
                        continue
                    if not self.exits("标志背包锁定格子"):
                        self.setup = "滑动背包"
                        continue
                    self.setup = "解锁背包格子"
                case "解锁背包格子":
                    self.touch("标志背包锁定格子")
                    self.touch("按钮解锁")
                    self.logs(f"解锁背包 {self.event["解锁背包次数"]} 次")
                    self.event["解锁背包次数"] += 1
                    self.setup = "检测背包格子"

        return None
