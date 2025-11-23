from script.task.basis.ClassicTask import ClassicTask


class RiverTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("山河器超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("山河器完成")
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
                    if self.exits("界面山河器"):
                        self.setup = 4
                        continue
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品山河器")

                case 4:
                    if self.touch("按钮山河器前往探索"):
                        self.logs("前往探索山河器")
                        self.arrive()
                        self.touch("按钮大世界拾取")
                        self.logs("拾取")
                        self.keepAlive()
                        self.backToMain()
                        self.unstuck()
                        self.setup = 3
                        continue

                    if self.touch("按钮山河器免费搜索"):
                        self.logs("搜索免费山河器")
                        self.defer(count=5)
                        self.touch("标志山河器日晷")
                        continue

                    self.setup = 0




        return None
