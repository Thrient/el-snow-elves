import re

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

            match self.setup:
                # 任务结束
                case 0:
                    self.backToMain()
                    self.logs("采集任务完成")
                    return 0
                # 位置检测
                case 1:
                    # 前往采集地图
                    self.areaGo(self.event[2], unstuck=True)
                    self.setup = 2
                # 队伍检测
                case 2:
                    self.teamDetection()
                    self.setup = 3
                case 3:
                    if self.checkSwitchBranchLine() == 2:
                        self.toCollectionLocation()

                    b = self.collection()
                    if b == 0:
                        self.setup = 0
                        continue
                    elif b == 1:
                        continue
                    elif b == 3:
                        if self.exits("界面交易") is not None:
                            if self.taskConfig.autoBuyTool:
                                self.logs("购买工具")
                                self.buy("摆摊购买")
                                continue
                            self.logs("无工具结束任务")
                            self.setup = 0
                        continue

    def checkSwitchBranchLine(self):
        """
        检查并执行换线操作

        该函数根据任务配置和当前事件状态来决定是否需要换线操作，
        如果需要换线则调用相应的换线方法并更新事件状态

        参数:
            无

        返回值:
            2: 前往新坐标
        """
        # 检查换线目标是否超出范围
        if self.event[4] >= self.taskConfig.collectionSwitch or not self.event[3]:
            self.event[4] = 1
            return 2
            # 如果换线只有一线默认不换线 跳过后续执行
        if self.taskConfig.collectionSwitch == 1:
            return
        self.switchBranchLine(self.event[4])
        self.event[4] += 1

    def collection(self):
        """
        采集功能函数

        该函数用于执行大世界中的采集操作，包括判断采集物是否存在以及执行采集加速操作

        参数:
            无

        返回值:
            0: 任务结束
            1: 购买工具
            3: 加速失败
        """
        # 判断采集次数
        if self.taskConfig.collectionCount < self.event[5]:
            return 0
        # 判断是否有采集物
        if self.touch("按钮大世界采集", "按钮大世界砍伐", "按钮大世界挖矿", "按钮大世界拾取", "按钮大世界搜查",
                      timeout=0) is None:
            return
        # 采集加速
        if self.wait("标志大世界采集加速", box=(590, 370, 685, 450), overTime=10) is None:
            return 3
        self.mouseClick((665, 470))
        self.logs(f"采集 {self.event[5]}次")
        self.event[5] += 1
        self.defer(5)
        self.closeRewardUi(3)

    def toCollectionLocation(self):
        """
        前往采集坐标位置

        该函数根据事件数据中的坐标信息，验证坐标格式并前往指定的采集位置。
        函数会检查坐标列表是否为空，验证索引有效性，检验坐标格式，最后调用
        areaGo方法前往目标坐标。

        参数:
            无

        返回值:
            None: 当坐标列表为空或坐标格式不正确时
            False: 当坐标格式验证失败时
            无明确返回值: 正常执行完毕时
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
        pattern = r'^\d+#\d+$'
        #  验证坐标格式
        if not bool(re.match(pattern, str(__coord))):
            return False
        # 前往坐标
        self.logs(f"前往采集坐标 {__coord.split("#")[0]}:{__coord.split("#")[1]}")
        self.areaGo(self.event[2], __coord.split("#")[0], __coord.split("#")[1])
