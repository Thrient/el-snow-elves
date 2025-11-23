from script.task.basis.ClassicTask import ClassicTask


class UrgentDeliveryTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "buy_counter": 0.0,  # 购买失败计数器
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("江湖急送超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("江湖急送完成")
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
                    self.openFaction()
                    self.touch("按钮帮派势力")
                    self.touch("按钮帮派江湖急送")

                    if self.exits("标志江湖急送订单上限"):
                        self.setup = 0
                        continue
                    self.touch("按钮帮派抢单")
                    self.backToMain()
                    self.setup = 4
                case 4:
                    self.activatedTask("按钮任务外卖", model="江湖")

                    if self.exits("按钮江湖急送菜品送达"):
                        self.touch("按钮江湖急送菜品送达")
                        self.defer(7)
                        self.touch("按钮江湖急送确认")
                        self.closeRewardUi(count=5)
                        self.setup = 3
                        continue

                    if self.exits("按钮江湖急送前往购买"):
                        if self.event["buy_counter"] >= 3:
                            self.touch("按钮江湖急送放弃订单")
                            self.touch("按钮确定")
                            self.event["buy_counter"] = 1
                            self.setup = 3
                            continue

                        self.touch("按钮江湖急送前往购买", x=100)
                        self.touch("按钮神厨商会", y=-75)
                        self.defer(2)
                        self.touch("按钮江湖急送菜品标签")
                        results = self.exits("标志江湖急送标签", find_all=True)
                        self.click_mouse(pos=(1330, 745))

                        for index in range(len(results) + 1):
                            if self.exits("标志江湖急送符合"):
                                self.touch("标志江湖急送符合", x=10, y=10)
                                self.touch("按钮江湖急送购买")
                                self.touch("按钮确定")
                                break
                            if index == len(results):
                                break
                            self.touch("按钮江湖急送菜品标签")
                            self.click_mouse(pos=results[index])
                            self.click_mouse(pos=(1330, 745))

                        self.backToMain()
                        self.event["buy_counter"] += 1

                    if self.exits("按钮江湖急送领取食盆"):
                        self.touch("按钮江湖急送领取食盆")

                        self.arrive()
                        self.touch("按钮江湖急送菜品打包")

                        self.touch("按钮江湖急送选择菜品", x=-145)
                        self.touch("按钮江湖急送选择")
                        self.touch("按钮江湖急送选择菜品")
                        self.touch("按钮确定")
        return None
