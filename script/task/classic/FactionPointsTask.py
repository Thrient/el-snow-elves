from script.task.basis.classic.ClassicTask import ClassicTask


class FactionPointsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件类型定义
        self.event = {
            "advance_counter": 0
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            "帮派领地": {"advance_counter": 0}
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("帮派积分超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.exitInstance()
                    self.logs("帮派积分完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.locationDetection()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    # self.teamDetection()
                    self.setup = "帮派共舞"
                case "帮派共舞":
                    from script.core.TaskFactory import TaskFactory
                    cls = TaskFactory.instance().create(self.taskConfig.model, "帮派积分跳舞")
                    with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
                        obj.execute()
                    self.setup = "帮派领地"
                case "帮派领地":
                    self.openFaction()
                    self.touch("按钮帮派领地")
                    self.touch("按钮帮派前往领地")
                    self.arrive()
                    self.resetLens()
                    self.setup = "等待清扫按钮"
                case "等待清扫按钮":
                    if self.event["advance_counter"] >= 8:
                        self.exitInstance()
                        self.setup = "帮派领地"
                        continue
                    self.event["advance_counter"] += 1
                    self.click_key(key=self.taskConfig.keyList[16], press_down_delay=0.04)

                    self.setup = "点击清扫按钮"
                case "点击清扫按钮":
                    if not self.touch("按钮大世界清扫", "按钮大世界清扫_V1", times=3):
                        self.setup = "等待清扫按钮"
                        continue
                    self.setup = "等待清扫结束"
                case "等待清扫结束":
                    coord = self.exits("按钮大世界清扫_V1", times=5)
                    if not coord:
                        continue
                    if self.exits_not_color(x=coord[-1][0] + 30, y=coord[-1][1], target_color=(255, 255, 255),
                                            tolerance=10, times=5):
                        self.setup = "任务结束"
                        continue

        return None
