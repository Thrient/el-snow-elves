import base64

import cv2
from airtest.aircv.utils import pil_2_cv2

from script.config.Config import Config
from script.task.basis.BasisTask import BasisTask
from abc import ABC

from script.utils.Utils import Utils


class ClassicTask(BasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def waitMapLoading(self):
        """
        等待地图加载完成

        该函数通过检查特定标志来判断地图是否加载完成，最多等待3次循环

        参数:
            self: 类实例对象

        返回值:
            无返回值
        """
        __count = 0
        self.logs("等待地图加载")
        while not self.finished.is_set():
            # 检查是否正在加载地图，如果是则继续等待
            if self.exits("标志地图加载", "标志地图加载_1") is not None:
                continue
            # 限制循环次数，防止无限等待
            if __count > 1:
                break
            __count += 1
        self.logs("地图加载结束")

    def locationDetection(self):
        """
        位置检测函数

        该函数用于执行位置检测操作，记录日志并移动到指定区域

        参数:
            self: 类实例对象

        返回值:
            无
        """
        self.logs("位置检测")
        self.areaGo("金陵")

    def areaGo(self, area, x=None, y=None):
        """
        前往指定区域

        :param area: 目标区域名称
        :param x: 目标区域的x坐标，如果为None则使用默认坐标
        :param y: 目标区域的y坐标，如果为None则使用默认坐标
        :return: 无返回值
        """
        __coordinate = {
            "金陵": ("571", "484"),
        }

        # 如果未指定坐标，则使用默认坐标
        x = __coordinate[area][0] if x is None else x
        y = __coordinate[area][1] if y is None else y

        self.logs(f"{area}区域前往")
        self.openMap()

        # 检查是否已经处于目标区域
        if self.exits(f"标志地图{area}坐标") is not None:
            self.logs(f"当前已处于{area}区域")
            self.closeMap()
            return

        # 执行前往区域的操作流程
        self.touch("按钮地图世界区域")
        self.touch(f"按钮地图{area}区域")
        self.coordinateInput(x, y)
        self.touch("按钮地图前往区域")
        self.closeMap()
        self.arrive()

    def coordinateInput(self, x, y):
        """
        输入坐标值到地图坐标输入框中

        参数:
            x: 横坐标值
            y: 纵坐标值
        """
        # 停止自动寻路功能
        self.touch("按钮地图停止寻路")

        # 展开坐标输入面板
        self.touch("按钮地图坐标展开")

        # 输入横坐标值
        self.touch("按钮地图横坐标")
        self.input(x)

        # 输入纵坐标值
        self.touch("按钮地图纵坐标")
        self.input(y)

    def teamDetection(self):
        """
        队伍检测功能函数

        该函数用于检测当前队伍状态，如果队伍未创建则进行相应处理
        包括打开队伍界面、退出队伍、确认操作和关闭队伍界面等步骤

        参数:
            无

        返回值:
            无
        """
        self.logs("队伍检测")
        self.openTeam()
        # 检查队伍是否已创建，如果已创建则直接返回
        if self.exits("标志队伍未创建") is None:
            self.touch("按钮队伍退出")
            self.touch("按钮队伍确定")
        self.closeTeam()

    def buy(self, model):
        """
        执行购买操作

        :param model: 购买模式，可选值为"摆摊购买"或"商城购买"或"帮派仓库"
        :return: 无返回值
        """
        if model == "摆摊购买":
            __event = True
            # 交易购买循环逻辑
            while not self.finished.is_set():
                # 检查交易界面是否存在
                if self.exits("界面交易") is None:
                    return

                # 记录交易购买日志
                if __event is True:
                    __event = False
                    self.logs("摆摊购买")

                # 点击交易需求按钮并执行购买流程
                self.touch("按钮交易需求", x=130, y=35)
                if self.touch("按钮交易购买") is not None:
                    self.touch("按钮交易确定")

                self.closeStalls()

        if model == "商城购买":
            # 检查商城界面是否存在
            if self.exits("界面珍宝阁") is None:
                return
            # 记录商城购买日志并执行购买操作
            self.logs("商城购买")
            self.mouseClick((990, 690), count=8)

            # 关闭商城界面
            self.closeMall()

        if model == "帮派仓库":
            if self.exits("界面帮派仓库") is None:
                return
            self.logs("帮派仓库提交")
            self.touch("按钮帮派仓库提交")
            self.closeBanStore()

    def closeRewardUi(self, count=1):
        """
        关闭奖励界面

        参数:
            count (int): 关闭界面的操作次数，默认为1
        """
        # 关闭当前界面，指定奖励界面的坐标区域
        self.closeCurrentUi(count=count, box=(905, 201, 1118, 454))

    def closeCurrentUi(self, count=1, box=Config.BOX):
        """
        关闭当前用户界面

        :param count: 关闭次数，默认为1次
        :param box: 搜索区域配置，默认使用Config.BOX
        :return: 无返回值
        """
        self.logs("关闭当前界面")
        # 循环执行关闭操作，直到达到指定次数或无法找到关闭按钮
        for i in range(count):
            if self.touch("按钮关闭", box=box) is None:
                return

    def backToMain(self):
        """
        返回主界面函数

        该函数用于从当前界面返回到主界面，通过不断关闭当前UI直到检测到主界面按钮

        参数:
            self: 类实例本身

        返回值:
            无返回值
        """
        self.logs("返回主界面")
        # 循环关闭当前界面直到返回主界面或任务完成
        while not self.finished.is_set():
            # 检查是否已经回到主界面（通过检测"按钮世界挂机"是否存在）
            if self.exits("按钮世界挂机") is not None:
                break
            self.keyClick("TAB")
            # 关闭当前打开的界面
            self.closeCurrentUi()

    def closeBanStore(self):
        """
        关闭帮派仓库界面

        该函数用于关闭当前打开的帮派仓库界面

        参数:
            无

        返回值:
            无
        """
        self.logs("关闭帮派仓库")
        # 检查帮派仓库界面是否存在，不存在则直接返回
        if self.exits("界面帮派仓库") is None:
            return
        # 关闭当前界面
        self.closeCurrentUi()

    def closeStalls(self):
        """
        关闭摆摊功能

        该函数用于关闭当前的摆摊界面

        参数:
            无

        返回值:
            无
        """
        self.logs("关闭摆摊")
        # 检查交易界面是否存在，如果不存在则直接返回
        if self.exits("界面交易") is None:
            return
        # 关闭当前用户界面
        self.closeCurrentUi()

    def closeMall(self):
        """
        关闭珍宝阁界面

        该函数用于关闭当前打开的珍宝阁界面

        参数:
            self: 类实例本身

        返回值:
            无返回值
        """
        self.logs("关闭珍宝阁")
        # 检查珍宝阁界面是否存在，不存在则直接返回
        if self.exits("界面珍宝阁") is None:
            return
        # 执行关闭当前界面的操作
        self.closeCurrentUi()

    def closeBuddy(self):
        """
        关闭好友界面功能函数

        该函数用于关闭当前打开的好友界面，如果当前不在好友界面则不执行任何操作

        参数:
            self: 类实例本身

        返回值:
            无返回值
        """
        self.logs("关闭好友")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if self.exits("界面好友") is None:
            return
        self.closeCurrentUi()

    def openBuddy(self):
        """
        打开好友界面功能函数

        该函数用于打开游戏副本中的好友界面，首先会检查好友界面是否已经打开，
        如果未打开则通过按键操作来打开界面。

        参数:
            self: 类实例对象，包含游戏相关的操作方法和属性

        返回值:
            无返回值
        """
        self.logs("打开好友")
        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if self.exits("界面好友") is None:
            self.keyClick("H")

    def closeMap(self):
        """
        关闭地图界面

        该函数用于关闭当前打开的地图界面

        Returns:
            None
        """
        self.logs("关闭地图")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if self.exits("标志地图当前坐标") is None:
            return
        self.closeCurrentUi()

    def openMap(self):
        """
        打开地图界面函数

        该函数用于打开游戏中的地图界面，首先记录日志，然后检查地图界面是否已经打开，
        如果未打开则通过按键操作来打开地图界面

        参数:
            self: 类实例本身

        返回值:
            无
        """
        self.logs("打开地图")
        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if self.exits("标志地图当前坐标") is None:
            self.keyClick("M")

    def closeTeam(self):
        """
        关闭队伍界面

        该函数用于关闭当前打开的队伍界面

        参数:
            无

        返回值:
            无
        """
        self.logs("关闭队伍")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if self.exits("界面队伍") is None:
            return
        self.closeCurrentUi()

    def openTeam(self):
        """
        打开队伍界面函数

        该函数用于打开游戏中的队伍界面，如果队伍界面未开启则通过按键T来打开
        """
        self.logs("打开队伍")
        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if self.exits("界面队伍") is None:
            self.keyClick("T")

    def closeBackpack(self):
        """
        关闭背包界面

        该函数用于关闭当前打开的背包界面

        Returns:
            无返回值
        """
        self.logs("关闭背包")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if self.exits("界面物品") is None:
            return
        self.closeCurrentUi()

    def openBackpack(self):
        """
        打开背包界面

        该函数用于打开游戏中的背包界面，如果当前未处于物品界面，
        则通过按键'B'来打开背包。

        参数:
            self: 类实例本身

        返回值:
            无
        """
        self.logs("打开背包")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if self.exits("界面物品") is None:
            self.keyClick("B")

    def arrive(self):
        """
        等待到达目标位置的函数

        该函数通过检查特定标志来判断是否正在寻路或加载地图，
        如果检测到这些状态则继续等待，直到完成或超时。

        参数:
            self: 类实例对象

        返回值:
            无返回值
        """
        __count = 0
        self.logs("等待寻路结束")
        while not self.finished.is_set():
            # 检查是否正在寻路中，如果是则继续等待
            if self.exits("标志寻路中") is not None:
                continue
            # 检查是否正在加载地图，如果是则继续等待
            if self.exits("标志地图加载", "标志地图加载_1") is not None:
                continue
            # 限制循环次数，防止无限等待
            if __count > 3:
                break
            __count += 1
        self.logs("寻路结束")

    def switchCharacterDefault(self):
        """
        切换角色默认设置功能函数

        该函数用于执行切换角色默认设置的完整流程，包括返回主界面、打开背包、
        访问物品属性界面并设置角色信息等操作。

        参数:
            无

        返回值:
            无
        """
        self.logs("设置角色信息")
        self.backToMain()
        self.openBackpack()
        self.touch("按钮物品属性")
        self.setCharacterInfo()
        self.backToMain()

    def setCharacterInfo(self):
        """
        设置并发送角色信息到前端界面
        该函数截取游戏窗口中的角色信息区域，将其转换为base64编码的图片数据，
        然后通过信号发射机制发送给前端界面进行显示更新

        参数:
            self: 类实例对象，包含windowConsole、window和hwnd等属性

        返回值:
            无返回值
        """
        # 截取角色信息区域并转换图像格式
        character = pil_2_cv2(self.windowConsole.captureWindow().crop((742, 158, 892, 186)))

        # 将图像编码为PNG格式的二进制数据
        _, buffer = cv2.imencode('.png', character)

        # 将图像数据转换为base64编码并发送到前端界面
        Utils.sendEmit(self.window, "API:UPDATE:CHARACTER",
                       character=f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}", hwnd=self.hwnd)
