from script.task.basis.ClassicTask import ClassicTask


class ChivalryShoutTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件变量字典
        self.event = {
            "shout_count": 1,  # 侠缘喊话次数计数器
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("侠缘喊话超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("侠缘喊话完成")
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
                    self.openBuddy()
                    self.touch("按钮好友联系人")
                    self.touch("标志好友输入编号或昵称")
                    self.input(self.taskConfig.chivalryNameOrNumber)
                    self.touch("按钮好友搜索")
                    self.mouseClick((290, 333))
                    self.setup = 4
                case 4:
                    if self.event["shout_count"] > self.taskConfig.chivalryShoutCount:
                        self.closeBuddy()
                        self.setup = 0
                        continue

                    self.touch("标志好友输入文字")
                    self.input("日出日落都浪漫, 有风无风都自由")
                    self.touch("按钮好友发送")
                    self.logs(f"侠缘喊话 {self.event["shout_count"]} 次")
                    self.event["shout_count"] += 1
                    self.defer(3)
        return None
