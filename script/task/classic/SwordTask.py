import time

from script.task.basis.ClassicTask import ClassicTask


class SwordTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "sword_counter": 1,  # 单人论剑次数计数器,
            "is_prepare": False,  # 准备状态
            "check_timer": 0.0  # 场景检测计时器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            5: {"check_timer": lambda: time.time()},
            7: {"is_prepare": False},
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 3:
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
                    self.setup = 5
                case 3:
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动纷争")

                    self.touch("按钮活动华山论剑", "按钮活动萌芽论剑", x=-50, y=45)

                    self.setup = 4
                case 4:
                    if self.exits("界面单人论剑") is None:
                        self.setup = 5
                        continue

                    if self.exits("按钮单人论剑取消匹配") is None:
                        self.touch("按钮单人论剑匹配", seconds=None)

                    if self.exits("按钮确认") is not None:
                        self.touch("按钮确认", seconds=None)

                case 5:
                    if self.taskConfig.swordFightCount < self.event["sword_counter"]:
                        self.setup = 0
                        continue

                    if time.time() - self.event["check_timer"] > 20:
                        if self.exits("界面单人论剑") is not None:
                            self.setup = 4
                            continue
                        self.setup = 3
                        continue

                    if self.exits("标志单人论剑匹配成功") is not None:
                        self.defer(count=2)
                        self.waitMapLoading()
                        self.setup = 6
                        continue

                    if self.exits("标志单人论剑我方", "标志单人论剑敌方", "标志单人论剑我方_V1", "标志单人论剑敌方_V1") is not None:
                        self.setup = 6
                        continue
                case 6:
                    self.logs(f"单人论剑第 {self.event["sword_counter"]} 次")
                    self.event["sword_counter"] += 1
                    self.setup = 7
                case 7:
                    # 检查是否处于论剑场景
                    if self.exits("标志单人论剑我方", "标志单人论剑敌方","标志单人论剑我方_V1", "标志单人论剑敌方_V1") is None:
                        self.setup = 8
                        continue

                    # 判断是否主动退出
                    if self.taskConfig.swordFightInitiativeExit:
                        self.touch("按钮副本退出")
                        self.touch("按钮确定")
                        self.waitMapLoading()
                        self.setup = 5
                        continue

                    if self.event["is_prepare"]:
                        continue

                    self.touch("按钮华山论剑准备", post_delay=0)
                    self.event["is_prepare"] = True
                    self.click_key(key=self.taskConfig.keyList[16], press_down_delay=3)
                    self.autoFightStart()
                case 8:
                    # 点击华山论剑离开按钮
                    self.touch("按钮华山论剑离开", seconds=15)
                    # 停止自动战斗模式
                    self.autoFightStop()
                    # 等待地图加载完成
                    self.waitMapLoading()
                    self.setup = 5

        return None
