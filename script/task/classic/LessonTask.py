import time

from script.task.basis.ClassicTask import ClassicTask


class LessonTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "last_activated_time": 0.0,  # 上次激活任务时间
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("课业任务超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.logs("课业任务完成")
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
                    self.touch("按钮活动江湖")

                    if self.touch("按钮活动止杀", "按钮活动锻心", "按钮活动问卜", "按钮活动漱尘", "按钮活动归义",
                                  "按钮活动濯剑", "按钮活动吟风", "按钮活动悟禅", "按钮活动含灵", "按钮活动寻道",
                                  "按钮活动观梦", "按钮活动起茶", y=45) is None:
                        self.logs("课业任务已经完成")
                        self.setup = 0
                        continue

                    self.touch("按钮课业前往", box=(178, 443, 399, 582))
                    self.arrive()
                    self.touch("按钮课业课业", "按钮课业悟禅")
                    self.touch("按钮课业确定")
                    self.setup = 4
                case 4:
                    if self.exits("界面止杀", "界面锻心", "界面问卜", "界面漱尘", "界面归义",
                                  "界面濯剑", "界面吟风", "界面悟禅", "界面含灵", "界面寻道",
                                  "界面观梦", "界面起茶") is None:
                        self.logs("前往接取课业")
                        self.backToMain()
                        self.setup = 3
                        continue

                    if self.exits("标志课业已接取") is not None:
                        self.logs("课业任务已接取")
                        self.setup = 5
                        self.backToMain()
                        continue

                    if self.exits("按钮课业困难") is not None:
                        self.logs("选择困难课业")
                        self.touch("按钮课业困难")
                        self.setup = 5
                        self.backToMain()
                        continue
                    self.logs("刷新课业")
                    self.touch("按钮课业刷新", x=-50)
                    self.touch("按钮确定")
                case 5:
                    # 　定时激活任务
                    if time.time() - self.event["last_activated_time"] > 90:
                        self.event["last_activated_time"] = time.time()
                        self.activatedTask("按钮任务止杀", "按钮任务锻心", "按钮任务问卜", "按钮任务漱尘", "按钮任务归义", "按钮任务濯剑", "按钮任务吟风", "按钮任务悟禅", "按钮任务含灵", "按钮任务寻道", "按钮任务观梦", "按钮任务起茶", model="江湖")

                    # 商城购买
                    if self.exits("按钮商城购买") is not None:
                        self.touch("按钮商城购买", y=-75)

                    # 摆摊购买
                    if self.exits("按钮摆摊购买") is not None:
                        self.touch("按钮摆摊购买", y=-75)

                    # 检查商城购买
                    if self.buy("摆摊购买") or self.buy("商城购买"):
                        self.event["last_activated_time"] = time.time() - 90

                    # 杂货商人
                    if self.exits("界面杂货商人") is not None:
                        self.click_mouse(pos=(1018, 625))

                    # 答题
                    if self.exits("标志课业答题") is not None:
                        self.closeCurrentUi()

                    # 对话
                    if self.exits("标志对话卷轴") is not None:
                        self.touch("标志对话卷轴")

                    # 担水
                    if self.exits("标志课业一大桶水") is not None:
                        self.touch("按钮使用")

                    if self.exits("按钮课业一键提交") is not None:
                        self.touch("按钮课业一键提交")

                    if self.exits("标志课业完成") is not None:
                        self.touch("按钮确定")
                        self.closeRewardUi(5)
                        self.setup = 0

        return None
