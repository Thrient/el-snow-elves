from script.task.basis.ClassicTask import ClassicTask


class ChefIngredientsTask(ClassicTask):
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
                self.logs("神厨食材超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("神厨食材完成")
                    return 0
                # 位置检测
                case 1:
                    self.areaGo("中原", x=1272, y=1725)
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    self.resetLens()
                    self.click_key(key=self.taskConfig.keyList[16], press_down_delay=0.2)
                    self.setup = 4
                case 4:
                    self.touch("按钮大世界对话")
                    self.touch("按钮商人购买食材")
                    if self.exits("标志兑换商店批量购买") is not None:
                        self.touch("按钮兑换商店批量购买")

                    for text in self.taskConfig.chefIngredientsTags:
                        self.touch("标志输入名称搜索")
                        self.input(text=text)
                        self.touch("按钮搜索")
                        self.touch("按钮满")
                        self.click_mouse(pos=(1015, 630))
                        self.touch("按钮搜索返回")
                    self.backToMain()

                    self.setup = 5
                case 5:

                    self.touch("按钮大世界对话")
                    self.touch("按钮商人购买调料")
                    if self.exits("标志兑换商店批量购买") is not None:
                        self.touch("按钮兑换商店批量购买")

                    for text in self.taskConfig.chefSeasoningTags:
                        self.touch("标志输入名称搜索")
                        self.input(text=text)
                        self.touch("按钮搜索")
                        self.touch("按钮满")
                        self.click_mouse(pos=(1015, 630))

                        self.touch("按钮搜索返回")
                    self.backToMain()
                    self.setup = 0

        return None
