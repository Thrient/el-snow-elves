import random

from script.task.basis.ClassicTask import ClassicTask


class SkyCurtainElegantGardenTask(ClassicTask):
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
                self.logs("天幕雅苑超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("天幕雅苑完成")
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
                    self.move_mouse(start=(1245, 630), end=(1245, 330))
                    self.touch("按钮物品天幕雅苑")
                    self.touch("按钮天幕雅苑展馆排名")
                    self.move_mouse(start=(1050, 450), end=(500, 450), count=random.randint(1, 3))
                    self.touch("按钮天幕雅苑进入展馆")
                    self.waitMapLoading()

                    self.setup = 4
                case 4:
                    if not self.exits("按钮展馆时装试穿进行中"):
                        self.setup = 6
                        continue

                    if not self.exits("标志普通展厅任务"):
                        self.setup = 5
                        continue

                    self.touch("按钮展馆时装试穿进行中")
                    self.arrive()
                    self.resetLens()
                    self.click_key(key=self.taskConfig.keyList[16], press_down_delay=1.2)
                    self.touch("按钮大世界试穿")
                    self.setup = 6
                case 5:
                    self.touch("按钮展馆时装试穿进行中")
                    self.arrive()
                    self.touch("按钮大世界试穿")
                    self.setup = 6
                case 6:
                    if not self.exits("按钮展馆盖章打卡进行中"):
                        self.setup = 7
                        continue
                    self.touch("按钮展馆盖章打卡进行中")
                    self.arrive()
                    self.touch("按钮大世界签到盖章")
                    self.touch("按钮盖章确认")
                    self.backToMain()
                    self.setup = 7
                case 7:
                    self.closeRewardUi(count=5)
                    self.setup = 0
        return None
