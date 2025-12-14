import re
import time

from script.config.Config import Config
from script.task.basis.classic.ClassicTask import ClassicTask
from script.utils.Thread import thread


class AcquisitionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        self.event = {
            "采集方式": ["按钮大世界采集", "按钮大世界砍伐", "按钮大世界挖矿", "按钮大世界拾取", "按钮大世界搜查",
                         "按钮大世界垂钓", "按钮大世界市井喧闹", "按钮大世界繁花似锦", "按钮大世界空山鸟语"],
            "采集坐标": [],
            "采集坐标索引": 0,
            "采集地图": '',
            "采集换线计数": 1,
            "采集次数计数": 1
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    @thread(daemon=True)
    def popCheck(self):
        while not self._finished.is_set():
            self.closeRewardUi()

            time.sleep(1)

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 1800 * 2 * 12:
                self.logs("采集任务超时")
                return 0

            match self.setup:
                # 任务结束
                case "任务结束":
                    self.backToMain()
                    self.logs("采集任务完成")
                    return 0
                # 位置检测
                case "位置检测":
                    # self.locationDetection()
                    self.setup = "队伍检测"
                # 队伍检测
                case "队伍检测":
                    self.teamDetection()
                    self.setup = "采集信息解析"
                case "采集信息解析":
                    if self.taskConfig.collectionMode == "默认模式":
                        self.event["采集地图"] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][0]
                        self.event["采集坐标"] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][1]
                    elif self.taskConfig.collectionMode == "自定义模式":
                        self.event["采集地图"] = self.taskConfig.collectionMap
                        self.event["采集坐标"] = self.taskConfig.customCoordinatesTags
                    self.setup = "前往采集坐标"
                case "前往采集坐标":
                    if len(self.event["采集坐标"]) == 0:
                        self.setup = "采集工具判断"
                        continue
                    if self.event["采集坐标索引"] == 0:
                        self.event["采集坐标索引"] = 1
                        self.areaGo(self.event["采集地图"])
                        continue

                    # 验证索引长度是否超过坐标列表长度
                    self.event["采集坐标索引"] = self.event["采集坐标索引"] if self.event["采集坐标索引"] < len(
                        self.event["采集坐标"]) + 1 else 1
                    __coord = self.event["采集坐标"][self.event["采集坐标索引"] - 1]

                    # 更新坐标计数器
                    self.event["采集坐标索引"] += 1

                    #  验证坐标格式
                    if not bool(re.match(r'^\d+#\d+$', str(__coord))):
                        continue
                    # self.logs(f"前往采集坐标 {__coord.split("#")[0]}:{__coord.split("#")[1]}")
                    self.coordGo(__coord.split("#")[0], __coord.split("#")[1])
                    self.setup = "采集工具判断"
                case "采集换线":
                    if self.event["采集换线计数"] == self.taskConfig.collectionSwitch + 1:
                        self.event["采集换线计数"] = 1
                        self.setup = "前往采集坐标"
                        continue

                    self.switchBranchLine(self.event["采集换线计数"])
                    self.event["采集换线计数"] += 1
                    self.setup = "采集工具判断"
                case "采集工具判断":
                    if not self.exits("标志无采集工具"):
                        self.setup = "采集体力判断"
                        continue
                    if not self.taskConfig.autoBuyTool:
                        self.setup = "任务结束"
                        continue
                    self.touch("标志无采集工具")
                    self.buy("摆摊购买")
                    self.setup = "采集体力判断"
                case "采集体力判断":
                    if not self.exits("标志大世界体力上限"):
                        self.setup = "开始采集"
                        continue
                    if not self.taskConfig.autoEatEgg:
                        self.logs("无体力 结束任务")
                        self.setup = "任务结束"
                        continue
                    self.useBackpackArticles("一筐鸡蛋", self.taskConfig.autoEatEggCount)
                    self.setup = "开始采集"
                case "开始采集":
                    self.backToMain()
                    if not self.touch(*self.event["采集方式"]):
                        self.setup = "采集换线"
                        continue
                    self.setup = "采集加速"
                case "采集加速":
                    if self.wait("标志大世界采集加速", box=(625, 380, 655, 435), seconds=8):
                        self.click_mouse(pos=(665, 470))
                    self.setup = "采集完成判断"
                case "采集完成判断":
                    if self.exits_not_color(*self.event["采集方式"], x=-25, target_color=(255, 255, 255), tolerance=10):
                        self.setup = "采集次数判断"
                        continue
                    self.setup = "采集加速"
                case "采集次数判断":
                    self.logs(f"采集 {self.event["采集次数计数"]}次")
                    self.event["采集次数计数"] += 1

                    if self.event["采集次数计数"] >= self.taskConfig.collectionCount:
                        self.setup = "任务结束"
                        continue
                    self.setup = "开始采集"

        return None
