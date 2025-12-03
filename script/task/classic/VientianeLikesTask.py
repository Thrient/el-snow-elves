from script.task.basis.classic.ClassicTask import ClassicTask


class VientianeLikesTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "like_counter": 1

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("万象刷赞超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("万象刷赞完成")
                    return 0
                # 位置检测
                case 1:
                    self.areaGo(area="金陵", x=324, y=384, unstuck=True)
                    self.resetLens()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    self.click_mouse(pos=(1240, 715))
                    self.setup = 4
                case 4:
                    if not self.exits("界面场景"):
                        self.setup = 3
                        continue

                    self.touch("按钮场景万象")
                    self.touch("按钮场景拍照")
                    self.touch("按钮万象打卡")
                    self.touch("按钮万象上传打卡")
                    self.touch("按钮确定")
                    self.defer(count=5)
                    self.closeRewardUi()
                    self.setup = 5
                case 5:
                    self.touch("按钮拍照打卡立刻拍照", x=-235, y=-60)
                    self.touch("按钮拍照打卡立刻拍照")
                    self.logs(f"万象刷赞 {self.event["like_counter"]} 次")

                    if 30 <= self.event["like_counter"]:
                        self.setup = 0
                        continue

                    self.event["like_counter"] += 1
                    self.setup = 4

        return None
