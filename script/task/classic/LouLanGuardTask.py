from script.task.basis.classic.ClassicTask import ClassicTask


class LouLanGuardTask(ClassicTask):
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
                self.logs("楼兰守护超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.exitInstance()
                    self.logs("楼兰守护完成")
                    return 0
                # 位置检测
                case 1:
                    # self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    # self.teamDetection()
                    self.setup = 4
                case 3:
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品剑取楼兰")

                    self.setup = 4
                case 4:
                    if not self.exits("界面剑取楼兰"):
                        self.setup = 3
                        continue
                    self.touch("按钮剑取楼兰阵营")
                    self.touch("按钮剑取楼兰前往地图")
                    self.arrive()
                    self.touch("按钮梦回古西域")
                    self.defer(count=5)
                    self.setup = 5
                case 5:
                    self.move_mouse(start=(118, 300), end=(118, 452))
                    if not self.touch("标志剑取楼兰阵营守护", box=(0, 170, 265, 450)):
                        self.setup = 7
                        continue
                    self.arrive()
                    self.setup = 6
                case 6:
                    self.autoFightStart()
                    self.defer(count=18)
                    self.autoFightStop()
                    self.setup = 5
                case 7:
                    self.touch("标志剑取楼兰阵营守护", box=(0, 170, 265, 450))
                    self.arrive()
                    self.setup = 0

        return None
