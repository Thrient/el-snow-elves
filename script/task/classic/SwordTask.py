import time

from script.task.basis.classic.ClassicTask import ClassicTask


class SwordTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件类型定义
        self.event = {
            "匹配判断次数": 1,
            # "is_prepare": False,  # 准备状态
            # "check_timer": 0.0  # 场景检测计时器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            # 5: {"check_timer": lambda: time.time()},
            # 7: {"is_prepare": False},
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 3:
                self.logs("单人论剑超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("单人论剑完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "匹配次数判断"
                case "匹配次数判断":
                    if self.event["匹配判断次数"] > self.taskConfig.swordFightCount:
                        self.setup = "任务结束"
                        continue
                    self.setup = "匹配活动"
                case "匹配活动":
                    self.openActivity()
                    self.touch("按钮活动纷争")
                    self.touch("按钮活动华山论剑", "按钮活动萌芽论剑", x=-50, y=45)
                    self.setup = "等待匹配成功"
                case "等待匹配成功":
                    if not self.exits("界面单人论剑"):
                        self.setup = "检验匹配状态"
                        continue
                    self.touch("按钮单人论剑匹配", seconds=None)
                    self.touch("按钮确认", seconds=None)
                case "检验匹配状态":
                    if not self.exits("标志单人论剑匹配成功", seconds=8):
                        self.backToMain()
                        self.setup = "匹配次数判断"
                        continue
                    self.defer(4)
                    self.waitMapLoading()
                    self.setup = "开启自动战斗"
                case "开启自动战斗":
                    self.logs(f"单人论剑第 {self.event["匹配判断次数"]} 次")
                    if self.taskConfig.swordFightInitiativeExit:
                        self.touch("按钮副本退出")
                        self.touch("按钮确定")
                        self.waitMapLoading()
                        self.setup = "停止战斗"
                        continue
                    self.touch("按钮华山论剑准备", post_delay=0)
                    self.click_key(key=self.taskConfig.keyList[16], press_down_delay=3)
                    self.autoFightStart()
                    self.setup = "自动战斗中"
                case "自动战斗中":
                    if self.exits_not("按钮副本退出", "标志单人论剑我方", "标志单人论剑敌方", "标志单人论剑我方_V1", "标志单人论剑敌方_V1", times=8):
                        self.setup = "停止战斗"
                        continue
                case "停止战斗":
                    self.touch("按钮华山论剑离开")
                    self.autoFightStop()
                    self.waitMapLoading()
                    self.event["匹配判断次数"] += 1
                    self.setup = "匹配次数判断"


        return None
