from script.task.basis.classic.ClassicTask import ClassicTask
from script.utils.Thread import thread


class WeekDailyPack(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件类型定义
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    @thread(daemon=True)
    def popCheck(self):
        while not self._finished.is_set():
            self.closeDreamCub()

            if self.exits("标志副本提示"):
                self.touch("按钮取消")

            if self.exits("标志特殊弹窗_V1", "标志特殊弹窗_V2"):
                self.touch("按钮确定")

            self.defer()

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("周卡每日礼包超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.exitInstance()
                    self.backToMain()
                    self.logs("周卡每日礼包完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "每日礼包"
                case "每日礼包":
                    self.openProudSword()
                    self.touch("按钮特惠周卡")
                    self.click_mouse(pos=(130, 695))
                    self.setup = "任务结束"

        return None
