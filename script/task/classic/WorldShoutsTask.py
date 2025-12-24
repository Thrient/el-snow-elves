import time

from script.task.basis.classic.ClassicTask import ClassicTask


class WorldShoutsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件类型定义
        self.event = {
            "喊话列表": self.taskConfig.worldShoutsText.split("\n"),
            "喊话索引": 0,
            "喊话计时器": 0.0,
            "喊话计数器": 1,
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 12:
                self.logs("世界喊话超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("世界喊话完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "检测坐骑"
                case "检测坐骑":
                    self.logs("准备乘骑坐骑 若自动乘骑失败 请手动乘骑")
                    self.touch("按钮大世界坐骑")
                    self.setup = "喊话次数判断"
                case "喊话次数判断":
                    if self.event["喊话计数器"] > self.taskConfig.worldShoutsCount:
                        self.setup = "任务结束"
                        continue
                    self.setup = "解析喊话内容"
                case "解析喊话内容":
                    self.event["喊话索引"] = 0 if self.event["喊话索引"] >= len(self.event["喊话列表"]) else self.event["喊话索引"]
                    self.setup = "等待世界喊话"
                case "等待世界喊话":
                    if time.time() - self.event["喊话计时器"] < 34:
                        continue

                    if self.taskConfig.ordinaryWorldShouts:
                        self.ordinary_shout(self.event["喊话列表"][self.event["喊话索引"]])

                    if self.taskConfig.connectedWorldShouts:
                        self.connect_shout(self.event["喊话列表"][self.event["喊话索引"]])

                    self.logs(f"世界喊话 {self.event["喊话计数器"]} 次")
                    self.event["喊话计数器"] += 1
                    self.setup = "喊话次数判断"
        return None
