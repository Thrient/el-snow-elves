from script.task.basis.ClassicTask import ClassicTask


class ChivalryShoutTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        self.event = [1]

    def instance(self):
        return self

    def execute(self):
        self.setup = 1

        while not self.finished.is_set():

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
                    self.touch("标志好友输入文字")
                    self.input("日出日落都浪漫, 有风无风都自由")
                    self.touch("按钮好友发送")
                    self.logs(f"侠缘喊话 {self.event[0]} 次")
                    self.event[0] += 1

                    if self.event[0] > self.taskConfig.chivalryShoutCount:
                        self.closeBuddy()
                        self.setup = 0
                        continue
                    self.defer(3)
