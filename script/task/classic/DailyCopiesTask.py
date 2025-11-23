import time

from script.task.basis.ClassicTask import ClassicTask


class DailyCopiesTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件变量字典
        self.event = {
            "shout_timer": 0.0,  # 副本喊话时间计数器
            "activate_timer": 0.0,  # 副本激活计时器
            "stuck_timer": 0.0,  # 副本卡死计时器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            5: {"shout_timer": 0.0},
            8: {
                "activate_timer": 0.0,
                "stuck_timer": lambda: time.time(),
                "exit_check_counter": 0
            }
        }

    def execute(self):
        while not self._finished.is_set():

            if 1800 * 2 < self.timer.getElapsedTime():
                self.logs("日常副本超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("日常副本完成")
                    return 0
                # 位置检测
                case 1:
                    self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamCreate(model="日常")
                    self.setup = 5
                case 3:
                    if not self.exits("界面悬赏"):
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品活动")
                        if not self.exits("界面活动"):
                            continue
                        self.touch("按钮活动悬赏")
                        self.touch("按钮悬赏下页", x=50)
                        continue

                    if self.exits("标志悬赏接满"):
                        self.touch("按钮悬赏上页", x=-50)
                        self.setup = 4
                        continue
                    self.click_mouse(pos=(1100, 145), timeout=0.1)
                    if not self.exits("标志悬赏江湖纪事", box=(265, 175, 1190, 565)):
                        continue
                    self.touch("标志悬赏江湖纪事", y=325, timeout=0)
                    self.touch("按钮悬赏押金", timeout=0)
                case 4:
                    if not self.exits("按钮悬赏前往"):
                        self.setup = 0
                        continue
                    self.backToMain()
                    self.setup = 5
                case 5:
                    self.openTeam()
                    if len(self.exits("标志队伍空位", find_all=True)) <= 10 - self.taskConfig.copiesPeoples:
                        self.setup = 6
                        continue
                    self.touch("按钮队伍自动匹配")

                    if not self.touch("按钮队伍赛季喊话"):
                        self.touch("按钮队伍普通喊话", x=80)

                    if time.time() - self.event["shout_timer"] > 32:
                        self.event["shout_timer"] = time.time()
                        self.worldShouts(self.taskConfig.copiesShoutText, connected=True)
                case 6:
                    self.openTeam()
                    self.touch("按钮队伍进入副本")
                    self.touch("按钮确认")
                    self.setup = 7
                case 7:

                    if not self.exits("界面日常"):
                        self.setup = 8
                        continue
                    self.defer(count=5)
                    if not self.touch("按钮副本全体进入"):
                        self.setup = 6
                        continue

                    self.waitMapLoading()

                    self.setup = 8
                case 8:
                    if 360 * 2 - 20 < time.time() - self.event["stuck_timer"]:
                        self.teamDetection()
                        self.setup = 2
                        continue

                    if 360 < time.time() - self.event["activate_timer"]:
                        self.unstuck()
                        if not self.activatedTask("按钮任务副本", model="任务"):
                            continue
                        self.event["activate_timer"] = time.time()
                        continue

                    if self.exits("按钮副本跳过剧情"):
                        self.touch("按钮副本跳过剧情")

                    self.checkExit()
        return None

    def checkExit(self):
        if not self.exits("标志副本完成", "标志副本完成_V1"):
            self.event["exit_check_counter"] = 0
            return
        if 5 > self.event["exit_check_counter"]:
            self.event["exit_check_counter"] += 1
            self.defer()
            return

        self.backToMain()
        self.setup = 0
