from script.task.basis.classic.ClassicTask import ClassicTask


class ArrivalDetectionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "状态判断"
        # 事件类型定义
        self.event = {
            "到达检测计数": 0

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("到达检测超时")
                return 0

            match self.setup:
                case "状态判断":
                    if self.exits("标志寻路中"):
                        self.setup = "寻路中"
                        continue
                    if self.exits("标志地图加载", "标志地图加载_V1"):
                        self.setup = "过图中"
                        continue
                    self.event["到达检测计数"] = self.event["到达检测计数"] + 1
                    if self.event["到达检测计数"] > 8:
                        return 0
                case "寻路中":
                    if self.exits("标志寻路中"):
                        continue
                    self.setup = "状态判断"
                case "过图中":
                    if self.exits("标志地图加载", "标志地图加载_V1"):
                        continue
                    self.setup = "状态判断"

        return None
