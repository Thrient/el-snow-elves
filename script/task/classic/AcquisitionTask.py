import re
import time

from script.config.Config import Config
from script.task.basis.ClassicTask import ClassicTask
from script.utils.Thread import thread


class AcquisitionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {
            "collect_coord": [],  # 采集坐标 任务开始根据模式赋值采集坐标
            "collect_coord_index": 0,        # 采集坐标索引 用于切换采集坐标
            "collect_map": '',       # 采集地图 任务开始根据模式赋值采集地图
            "collect_change_line": 1,        # 采集换线 用于切换下一分线
            "collect_counter": 1         # 采集次数 用于记录采集次数
        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    @thread(daemon=True)
    def popCheck(self):
        while not self._finished.is_set() and not self.popCheckEvent.is_set():
            self.closeRewardUi()

            time.sleep(1)

    def execute(self):
        while not self._finished.is_set():

            if self.timer.getElapsedTime() > 600000:
                self.logs("采集任务超时")
                return 0

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("采集任务完成")
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
                    if self.taskConfig.collectionMode == "默认模式":
                        self.event["collect_map"] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][0]
                        self.event["collect_coord"] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][1]
                    elif self.taskConfig.collectionMode == "自定义模式":
                        self.event["collect_map"] = self.taskConfig.collectionMap
                        self.event["collect_coord"] = self.taskConfig.customCoordinatesTags

                    self.setup = 4
                case 4:
                    self.toCollectionLocation()
                    self.setup = 5
                case 5:
                    self.checkPhysicalStrength()

                    self.collect()

        return None

    def checkPhysicalStrength(self):
        """
        体力检测
        该函数用于检测当前角色的体力状态，判断是否需要进行补充体力操作。

        :param

        :return
            None
        """

        if self.exits("标志大世界体力上限") is None:
            return

        self.logs("吃鸡蛋")
        if not self.taskConfig.autoEatEgg:
            self.logs("无体力 结束任务")
            self.setup = 0
            return
        if not self.useBackpackArticles("一筐鸡蛋", self.taskConfig.autoEatEggCount):
            self.logs("缺少道具一筐鸡蛋 结束任务")
            self.setup = 0
            return

    def collect(self):
        """
        采集操作
        该函数执行采集任务的主要操作步骤，包括选择采集类型、购买采集加速、记录采集次数等。
        主要功能包括界面元素检测、按钮点击、等待操作和任务完成判断

        :param

        :return
            bool: 采集操作是否成功完成
        """

        if self.touch("按钮大世界采集", "按钮大世界砍伐", "按钮大世界挖矿", "按钮大世界拾取",
                      "按钮大世界搜查", "按钮大世界垂钓", "按钮大世界市井喧闹",
                      "按钮大世界繁花似锦", "按钮大世界空山鸟语") is None:
            # 换线更新坐标
            if self.taskConfig.collectionSwitch == 1:
                self.toCollectionLocation()
                return False

            # 重置换线计数器
            if self.event["collect_change_line"] == self.taskConfig.collectionSwitch + 1:
                self.event["collect_change_line"] = 1
                self.toCollectionLocation()
                return False

            # 换线操作
            self.switchBranchLine(self.event["collect_change_line"])
            self.event["collect_change_line"] += 1
            return False

        if self.buy("摆摊购买"):
            return False

        if self.wait("标志大世界采集加速", box=(625, 380, 655, 435), overTime=8) is not None:
            self.click_mouse(pos=(665, 470))

        self.logs(f"采集 {self.event["collect_counter"]}次")
        self.event["collect_counter"] += 1

        if self.event["collect_counter"] >= self.taskConfig.collectionCount:
            self.setup = 0
        return True



    def toCollectionLocation(self):
        """
        前往采集坐标位置

        该函数根据事件数据中的坐标信息，验证坐标格式并前往指定的采集位置。
        主要功能包括坐标有效性检查、坐标格式验证和角色移动控制。

        参数:
            self.event[0]: 当前坐标索引
            self.event[1]: 坐标列表
            self.event[2]: 区域信息
            self.event[3]: 是否已处理标记

        返回值:
            无返回值
        """
        # 如果坐标长度为0则跳过
        if len(self.event["collect_coord"]) == 0:
            return
        if len(self.event["collect_coord"]) == 1 and self.event["collect_coord_index"] != 0:
            return

        # 验证索引长度是否超过坐标列表长度
        self.event["collect_coord_index"] = self.event["collect_coord_index"] if self.event["collect_coord_index"] < len(self.event["collect_coord"]) else 0
        __coord = self.event["collect_coord"][self.event["collect_coord_index"]]
        # 更新坐标计数器
        self.event["collect_coord_index"] += 1
        pattern = r'^\d+#\d+$'
        #  验证坐标格式
        if not bool(re.match(pattern, str(__coord))):
            return
        # 前往坐标
        self.logs(f"前往采集坐标 {__coord.split("#")[0]}:{__coord.split("#")[1]}")
        self.areaGo(self.event["collect_map"], __coord.split("#")[0], __coord.split("#")[1], area_switch=self.event["collect_coord_index"] != 0)
