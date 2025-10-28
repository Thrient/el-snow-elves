import time

from script.task.basis.ClassicTask import ClassicTask


class FactionTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {
            "last_activated_time": 0.0,  # 上次激活任务时间
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }


    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("帮派任务超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("帮派任务完成")
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
                    self.touch("按钮物品活动")
                    self.touch("按钮活动帮派")

                    if self.touch("按钮活动帮派任务", y=45) is None:
                        self.logs("帮派任务已经完成")
                        self.setup = 0
                        continue

                    self.arrive()
                    self.touch("按钮帮派任务")
                    self.touch("按钮帮派任务确定")

                    self.setup = 4
                case 4:
                    # 　定时激活任务
                    if time.time() - self.event["last_activated_time"] > 90:
                        self.event["last_activated_time"] = time.time()
                        self.activatedTask("按钮任务帮派", model="江湖")

                    if self.exits("标志帮派任务下一轮") is not None:
                        self.touch("按钮取消")
                        self.click_mouse(pos=(0, 0))
                        self.closeRewardUi(5)
                        self.setup = 0

                    # 商城购买
                    if self.exits("按钮商城购买") is not None:
                        self.touch("按钮商城购买", y=-75)

                    # 摆摊购买
                    if self.exits("按钮摆摊购买") is not None:
                        self.touch("按钮摆摊购买", y=-75)

                    # 检查商城购买
                    if self.buy("摆摊购买") or self.buy("商城购买"):
                        self.event["last_activated_time"] = time.time() - 90

                    self.closeRewardUi()

                    self.touch("按钮帮派任务一键提交")

                    if self.exits("标志帮派任务完成") is not None:
                        self.click_mouse(pos=(0, 0))
                        self.closeRewardUi(5)
                        self.setup = 0
        return None
