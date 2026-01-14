import time

from script.task.basis.classic.ClassicTask import ClassicTask


class BountyMissionsTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件变量字典
        self.event = {
            "喊话计时器": 0.0,
            "任务激活计时器": 0.0,
            "脱离副本计时器": 0.0,
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            "进入副本": {
                "任务激活计时器": lambda: time.time(),
                "脱离副本计时器": lambda: time.time(),
            }
        }

    def execute(self):
        while not self._finished.is_set():

            if 1800 * 2 < self.timer.getElapsedTime():
                self.logs("日常副本超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.logs("日常副本完成")
                    return 0
                # 位置检测
                case "位置检测":
                    self.exitInstance()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamCreate(model="日常")
                    self.setup = "检查悬赏"
                case "检查悬赏":
                    self.openBounty()
                    if not self.exits("标志悬赏接满"):
                        self.setup = "进入悬赏分类"
                        continue

                    if not self.exits("按钮悬赏前往"):
                        self.setup = "任务结束"
                        continue

                    self.setup = "队员检测"
                case "进入悬赏分类":
                    self.touch("按钮悬赏开启分类显示", seconds=None)
                    self.click_mouse(pos=(1100, 145), timeout=0.1)
                    if not self.touch("标志悬赏日常分类", seconds=None):
                        continue

                    self.touch("按钮悬赏下页", x=50)
                    self.setup = "接取悬赏"
                case "接取悬赏":
                    if not self.exits("标志悬赏接满"):
                        self.click_mouse(pos=(1100, 145), timeout=0.1)
                        if not self.exits("标志悬赏江湖纪事", box=(265, 175, 1190, 565)):
                            continue
                        self.touch("标志悬赏江湖纪事", y=325, timeout=0)
                        self.touch("按钮悬赏押金", timeout=0)
                        continue
                    self.setup = "队员检测"
                case "队员检测":
                    self.openTeam()
                    if len(self.exits("标志队伍空位", find_all=True)) <= 10 - self.taskConfig.copiesPeoples:
                        self.setup = "进入副本"
                        continue

                    if time.time() - self.event["喊话计时器"] > 32:
                        self.event["喊话计时器"] = time.time()
                        self.setup = "世界喊话"
                        continue
                    self.touch("按钮队伍自动匹配")
                case "世界喊话":
                    self.ordinary_shout(self.taskConfig.copiesShoutText)
                    self.connect_shout(self.taskConfig.copiesShoutText)
                    self.setup = "队员检测"
                case "进入副本":
                    self.openTeam()
                    self.touch("按钮队伍进入副本")
                    self.touch("按钮确认")
                    self.setup = "等待队员确认"
                case "等待队员确认":
                    if not self.exits("界面日常"):
                        self.setup = "任务检测"
                        continue
                    self.defer(5)
                    self.logs("全体进入")
                    self.touch("按钮副本全体进入")
                    self.waitMapLoading()
                    self.setup = "任务检测"
                case "任务检测":
                    if not self.activatedTask("按钮任务副本", model="任务"):
                        self.setup = "队员检测"
                        continue
                    self.setup = "等待任务完成"
                case "等待任务完成":
                    if time.time() - self.event["任务激活计时器"] > 180 * 2:
                        self.unstuck()
                        self.staffDetection()
                        self.event["任务激活计时器"] = time.time()
                        self.setup = "任务检测"
                        continue

                    if time.time() - self.event["脱离副本计时器"] > 180 * 5:
                        self.setup = "中止副本"
                        continue

                    self.closeStalls()

                    if self.exits("按钮副本跳过剧情"):
                        self.touch("按钮副本跳过剧情")

                    if self.exits("标志副本完成", "标志副本完成_V1", times=5):
                        self.setup = "副本完成"
                        continue
                case "中止副本":
                    self.exitInstance()
                    self.staffDetection()
                    self.defer(300)
                    self.setup = "队员检测"
                case "副本完成":
                    self.exitInstance()
                    self.setup = "检查悬赏"
        return None
