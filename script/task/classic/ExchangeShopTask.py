from script.task.basis.ClassicTask import ClassicTask


class ExchangeShopTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 事件类型定义
        self.event = {
            "exchange_counter": 0  # 兑换商店计数器

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {
            3: {"exchange_counter": 0}
        }

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800:
                self.logs("兑换商店超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("兑换商店完成")
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
                    self.openExchangeShop()

                    self.setup = 4
                case 4:
                    if len(self.taskConfig.dailyExchangeList) == 0:
                        self.setup = 0
                        continue

                    if self.event["exchange_counter"] == len(self.taskConfig.exchangeShopList):
                        self.setup = 0
                        continue

                    __text = self.taskConfig.exchangeShopList[self.event["exchange_counter"]]
                    self.event["exchange_counter"] += 1
                    self.touch("标志输入框")

                    self.input(text=__text.split("#")[0])
                    self.touch("按钮搜索")

                    self.touch(f"标志{__text.split("#")[1]}")
                    self.touch("按钮满")
                    self.click_mouse(pos=(1160, 700))
                    self.touch("按钮搜索返回")

        return None

    # def exchange(self):
    #     if len(self.event["collect_coord"]) == 0:
    #         return
    #     if len(self.event["collect_coord"]) == 1:
