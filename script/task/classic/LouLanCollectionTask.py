from script.task.basis.classic.ClassicTask import ClassicTask


class LouLanCollectionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "camp_coord": (0, 0),
            "collect_counter": 1
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("楼兰采集超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("楼兰采集完成")
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
                    if self.exits("标志楼兰王室"):
                        self.event["camp_coord"] = (3626, 502)
                    elif self.exits("标志小西天"):
                        self.event["camp_coord"] = (1426, 2930)
                    elif self.exits("标志天狼会"):
                        self.event["camp_coord"] = (2365, 2991)
                    self.touch("按钮剑取楼兰前往地图")
                    self.arrive()
                    self.touch("按钮梦回古西域")
                    self.defer(count=5)
                    self.setup = 5
                case 5:
                    self.move_mouse(start=(118, 300), end=(118, 452))
                    if not self.exits("标志剑取楼兰阵营采集", box=(0, 170, 265, 450)):
                        self.setup = 0
                        continue
                    self.setup = 6
                case 6:
                    self.openMap()
                    self.coordinateInput(self.event["camp_coord"][0], self.event["camp_coord"][1])
                    self.touch("按钮地图前往区域")
                    self.closeMap()
                    self.arrive()
                    self.setup = 7
                case 7:
                    if not self.touch("按钮大世界收集") or 10 < self.event["collect_counter"]:
                        self.setup = 5
                        self.unstuck()
                        continue
                    self.event["collect_counter"] += 1
                    self.defer(count=3)

        return None
