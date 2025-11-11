import time

from script.task.basis.ClassicTask import ClassicTask


class DailyCopiesTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件变量字典
        self.event = {
            "shout_timer": 0.0,  # 副本喊话时间计数器
            "activate_timer": 0.0,  # 副本激活计时器
            "unstuck_timer": 0.0,  # 副本脱离卡死计时器
            "stuck_timer": 0.0,  # 副本卡死计时器
            "exit_check_counter": 0  # 副本退出判断计数器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            5: {"shout_timer": 0.0},
            7: {
                "activate_timer": 0.0,
                "unstuck_timer": lambda : time.time(),
                "stuck_timer": lambda : time.time(),
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
                    if self.exits("界面悬赏") is None:
                        self.openBackpack()
                        self.touch("按钮物品综合入口")
                        self.touch("按钮物品活动")
                        if self.exits("界面活动") is None:
                            continue
                        self.touch("按钮活动悬赏")
                        self.touch("按钮悬赏下页", x=50)
                        continue

                    if self.exits("标志悬赏接满") is not None:
                        self.touch("按钮悬赏上页", x=-50)
                        self.setup = 4
                        continue
                    self.click_mouse(pos=(1100, 145), timeout=0.1)
                    if self.exits("标志悬赏江湖纪事", box=(265, 175, 1190, 565)) is None:
                        continue
                    self.touch("标志悬赏江湖纪事", y=325, timeout=0)
                    self.touch("按钮悬赏押金", timeout=0)
                case 4:
                    if self.exits("按钮悬赏前往") is None:
                        self.setup = 0
                        continue
                    self.backToMain()
                    self.setup = 5
                case 5:
                    self.openTeam()
                    if len(self.exitsAll("标志队伍空位")) <= 10 - 1:
                        self.setup = 6
                        continue
                    self.touch("按钮队伍自动匹配_V1")

                    if time.time() - self.event["shout_timer"] > 32:
                        self.event["shout_timer"] = time.time()
                        self.worldShouts("悬赏十连来人!!!")
                case 6:
                    self.openTeam()
                    self.touch("按钮队伍进入副本")
                    self.touch("按钮确认")

                    self.waitMapLoading()

                    self.setup = 7
                case 7:
                    if 360 * 4 - 20 < time.time() - self.event["stuck_timer"]:
                        self.teamDetection()
                        self.setup = 2
                        continue

                    if 360 * 2 - 20 < time.time() - self.event["unstuck_timer"]:
                        self.event["unstuck_timer"] = time.time()
                        self.event["activate_timer"] = 0
                        self.unstuck()
                        continue

                    if 360 < time.time() - self.event["activate_timer"]:
                        if self.activatedTask("按钮任务副本", model="任务") is None:
                            continue
                        self.event["activate_timer"] = time.time()
                        continue

                    if self.exits("按钮副本跳过剧情") is not None:
                        self.touch("按钮副本跳过剧情")

                    self.checkExit()
        return None

    def checkExit(self):
        if self.exits("标志副本完成") is None:
            self.event["exit_check_counter"] = 0
            return
        if 5 > self.event["exit_check_counter"]:
            self.event["exit_check_counter"] += 1
            self.defer()
            return

        self.touch("按钮副本退出")

        if self.touch("按钮副本离开") is None:
            return
        self.waitMapLoading()
        self.setup = 0
