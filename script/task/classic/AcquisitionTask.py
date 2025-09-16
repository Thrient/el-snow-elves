import re
import time

from script.config.Config import Config
from script.task.basis.ClassicTask import ClassicTask


class AcquisitionTask(ClassicTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = 1
        # 事件类型定义
        # 0:采集坐标索引 用于切换采集坐标
        # 1:采集坐标 任务开始根据模式赋值采集坐标
        # 2:采集地图 任务开始根据模式赋值采集地图
        # 3:是否前往采集坐标判断 如果只有一条坐标前往一次后后续不在前往
        # 4:采集换线 用于切换下一分线
        # 5:采集次数 用于记录采集次数
        self.event = [0, [], '', False, 1, 1]
        self.init()

    def instance(self):
        return self

    def init(self):
        # 初始化擦剂坐标索引
        self.event[0] = 0
        # 赋值采集坐标
        if self.taskConfig.collectionMode == "默认模式":
            self.event[2] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][0]
            self.event[1] = Config.COLLECTION_ARTICLES_DICt[self.taskConfig.collectionArticles][1]
        elif self.taskConfig.collectionMode == "自定义模式":
            self.event[2] = self.taskConfig.collectionMap
            self.event[1] = self.taskConfig.customCoordinatesTags

    def execute(self):
        while not self.finished.is_set():

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
                    # 前往采集地图
                    self.areaGo(self.event[2], exits=True, unstuck=True)
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    self.toCollectionLocation()
                    self.setup = 4
                case 4:
                    if self.exits("标志大世界体力上限") is not None:
                        self.logs("吃鸡蛋")
                        if not self.taskConfig.autoEatEgg:
                            self.logs("无体力 结束任务")
                            self.setup = 0
                            continue
                        if not self.useBackpackArticles("一筐鸡蛋", self.taskConfig.autoEatEggCount):
                            self.logs("缺少道具一筐鸡蛋 结束任务")
                            self.setup = 0
                            continue
                        continue

                    if self.touch("按钮大世界采集", "按钮大世界砍伐", "按钮大世界挖矿", "按钮大世界拾取",
                                  "按钮大世界搜查", "按钮大世界垂钓", "按钮大世界市井喧闹",
                                  "按钮大世界繁花似锦", "按钮大世界空山鸟语") is not None:

                        if self.buy("摆摊购买"):
                            continue

                        if self.wait("标志大世界采集加速", box=(625, 380, 655, 435), overTime=8) is not None:
                            self.mouseClick((665, 470))

                        self.logs(f"采集 {self.event[5]}次")
                        self.event[5] += 1

                        if self.event[5] >= self.taskConfig.collectionCount:
                            self.setup = 0
                        continue

                    # 换线更新坐标
                    if self.taskConfig.collectionSwitch == 1:
                        self.toCollectionLocation()
                        continue

                    # 重置换线计数器
                    if self.event[4] == self.taskConfig.collectionSwitch + 1:
                        self.event[4] = 1
                        self.toCollectionLocation()
                        continue

                    # 换线操作
                    self.switchBranchLine(self.event[4])
                    self.event[4] += 1
                    continue

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
        if len(self.event[1]) == 0:
            return
        if len(self.event[1]) == 1 and self.event[3]:
            return
        self.event[3] = True
        # 验证索引长度是否超过坐标列表长度
        self.event[0] = self.event[0] if self.event[0] < len(self.event[1]) else 0
        __coord = self.event[1][self.event[0]]
        # 更新坐标计数器
        self.event[0] += 1
        pattern = r'^\d+#\d+$'
        #  验证坐标格式
        if not bool(re.match(pattern, str(__coord))):
            return
        # 前往坐标
        self.logs(f"前往采集坐标 {__coord.split("#")[0]}:{__coord.split("#")[1]}")
        self.areaGo(self.event[2], __coord.split("#")[0], __coord.split("#")[1], currentArea=True)
