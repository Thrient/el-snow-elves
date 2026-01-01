import datetime
import time

from script.task.basis.classic.ClassicTask import ClassicTask


class BonfireBarrierTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件变量字典
        self.event = {
            "匹配判断次数": 1
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 12:
                self.logs("烽火雁门关超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("烽火雁门关完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "活动时间校验"
                case "活动时间校验":
                    now = datetime.datetime.now()

                    if now.weekday() in [0, 1, 4]:
                        self.setup = "任务结束"
                        continue

                    if now.weekday() in [2, 5] and now.time() <= datetime.time(8, 0):
                        self.setup = "任务结束"
                        continue

                    if now.weekday() in [3, 6] and now.time() >= datetime.time(5, 0):
                        self.setup = "任务结束"
                        continue

                    self.setup = "匹配次数判断"
                case "匹配次数判断":
                    if self.event["匹配判断次数"] > 10:
                        self.setup = "任务结束"
                        continue
                    self.setup = "匹配活动"
                case "匹配活动":
                    self.openActivity()
                    self.touch("按钮活动纷争")
                    self.touch("按钮活动烽火雁门关", y=45)
                    self.setup = "等待匹配成功"
                case "等待匹配成功":
                    if not self.exits("界面战场"):
                        self.setup = "检验匹配状态"
                        continue
                    self.touch("按钮战场匹配", seconds=None)
                    self.touch("按钮确认", seconds=None)
                case "检验匹配状态":
                    if not self.exits("标志烽火雁门关匹配成功", seconds=8):
                        self.backToMain()
                        self.setup = "活动时间校验"
                        continue
                    self.defer(4)
                    self.waitMapLoading()
                    self.setup = "开启自动战斗"
                case "开启自动战斗":
                    self.logs(f"烽火雁门关第 {self.event["匹配判断次数"]} 次")
                    self.autoFightStart()
                    self.setup = "自动战斗中"
                case "自动战斗中":

                    if self.exits_not("按钮副本退出", "标志战场重伤", times=8):
                        self.setup = "停止战斗"
                        continue

                    self.touch("按钮烽火雁门关复活", seconds=None)

                case "停止战斗":
                    self.touch("按钮烽火雁门关离开")
                    self.autoFightStop()
                    self.waitMapLoading()
                    self.event["匹配判断次数"] += 1
                    self.setup = "活动时间校验"









        return None
