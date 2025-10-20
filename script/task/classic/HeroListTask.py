import time

from script.task.basis.ClassicTask import ClassicTask


class HeroListTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件变量字典
        self.event = {
            "hero_list_counter": 1,  # 江湖英雄榜次数计数器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("江湖英雄榜超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("江湖英雄榜完成")
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
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动纷争")
                    self.touch("按钮活动江湖英雄榜", y=45)
                    self.setup = 4
                case 4:
                    if self.exits("界面江湖英雄榜") is None:
                        if self.exits("标志江湖英雄榜匹配成功") is not None:
                            self.logs(f"江湖英雄榜第 {self.event["hero_list_counter"]} 次")
                            self.event["hero_list_counter"] += 1
                            self.defer(count=3)
                            self.waitMapLoading()
                            self.setup = 5
                            continue
                        self.setup = 3
                        continue

                    if self.exits("标志江湖英雄榜挑战次数", box=(767, 543, 1007, 674)) is not None:
                        self.setup = 0
                        continue

                    self.touch("按钮江湖英雄榜匹配", "按钮江湖英雄榜晋级赛")
                    self.touch("按钮江湖英雄榜确定", overTime=0.5)
                case 5:

                    if self.taskConfig.heroListInitiativeExit:
                        self.touch("按钮江湖英雄榜退出")
                        self.touch("按钮江湖英雄榜退出副本")
                    else:
                        self.touch("按钮江湖英雄榜准备")
                        self.keyClick("W", delay=3)
                        self.autoFightStart()

                    self.setup = 6
                case 6:

                    if self.exits("按钮江湖英雄榜离开") is not None \
                            or self.exits("标志江湖英雄榜我方", "标志江湖英雄榜敌方") is None:

                        self.autoFightStop()

                        self.touch("按钮江湖英雄榜离开")

                        if self.event["hero_list_counter"] > self.taskConfig.heroListCount:
                            self.setup = 0
                            continue

                        self.waitMapLoading()
                        self.setup = 4

                        continue
        return None
