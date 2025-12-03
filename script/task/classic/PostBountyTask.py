from script.task.basis.classic.ClassicTask import ClassicTask


class PostBountyTask(ClassicTask):
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
                self.logs("发布悬赏超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("发布悬赏完成")
                    return 0
                # 位置检测
                case 1:
                    # self.locationDetection()
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    self.openBackpack()
                    self.touch("按钮物品综合入口")
                    self.touch("按钮物品活动")
                    self.touch("按钮活动悬赏")
                    self.setup = 4
                case 4:
                    self.touch("按钮悬赏发布", click_mode="first")
                    self.touch("按钮发布悬赏下拉")
                    self.touch("按钮发布悬赏江湖行商")
                    self.touch("按钮悬赏发布悬赏")
                    self.touch("按钮确定")
                    self.closeCurrentUi(box=(826, 72, 1130, 255))

                    self.setup = 5
                case 5:
                    self.touch("按钮悬赏发布", click_mode="first")
                    self.touch("按钮发布悬赏下拉")
                    self.touch("按钮发布悬赏聚义平冤")
                    self.touch("按钮悬赏发布悬赏")
                    self.touch("按钮确定")
                    self.closeCurrentUi(box=(826, 72, 1130, 255))
                    self.setup = 0
        return None
