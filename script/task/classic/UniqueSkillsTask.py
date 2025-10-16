import re

from script.task.basis.ClassicTask import ClassicTask


class UniqueSkillsTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self.finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("行当绝活超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("行当绝活完成")
                    self.backToMain()
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 4
                case 3:
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.mouseMove((1245, 630), (1245, 330))
                    self.touch("按钮物品精进行当")
                    self.touch("按钮行当通用")
                    self.setup = 4
                case 4:
                    if self.exits("界面行当通用") is None:
                        self.setup = 3
                        continue
                    self.touch("按钮行当鉴宝")
                    self.arrive()
                    self.touch("按钮行当磨具打造", "按钮行当鞋裤制样", "按钮行当兵刃图样", "按钮行当服冠制样")
                    self.setup = 5
                case 5:
                    if self.exits("界面生产制作") is None:
                        self.setup = 4
                        continue
                    self.touch("按钮生产制作炼制全部")
                    self.setup = 6
                case 6:
                    if self.exits("界面生产制作") is None:
                        self.setup = 4
                        continue

                    if self.exits("标志行当炼制中") is not None:
                        continue

                    self.setup = 0





        return None
