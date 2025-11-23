import base64
import threading
import time
from abc import ABC
from collections import deque
from threading import Event

import cv2
from airtest.aircv.utils import pil_2_cv2

from script.config.Config import Config
from script.task.basis.BasisTask import BasisTask
from script.utils.Api import api
from script.utils.Thread import thread


class ClassicTask(BasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动战斗
        self.autoFightEvent = Event()
        # 世界喊话设置
        self.WorldShoutsTextList = self.taskConfig.worldShoutsText.split("\n")
        self.WorldShoutsIndex = 0
        self.popCheck()

    def __enter__(self):
        api.on("API:SCRIPT:FINISH", self.finish)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        api.emit("API:SCRIPT:FINISH")
        api.off("API:SCRIPT:FINISH", self.finish)

    @thread(daemon=True)
    def popCheck(self):
        while not self._finished.is_set():
            self.closeDreamCub()

            if self.exits("标志副本提示"):
                self.touch("按钮取消")

            self.defer()

    def instance(self):
        """
        返回当前实例对象。

        该方法通常用于获取当前类的实例本身，便于链式调用或接口兼容。

        Returns:
            self: 当前实例对象
        """
        return self

    def resetLens(self):
        """
            重置镜头
        :return:
        """
        self.backToMain(exclude_branches=["副本退出"])
        self.click_mouse(pos=(1330, 715))
        self.touch("按钮大世界镜头重置")
        self.click_mouse(pos=(1330, 715))

    def action(self, action):
        """
        执行指定的动作

        参数:
            action (str): 要执行的动作名称

        返回值:
            无
        """
        # 检查是否为打开背包动作
        if "打开背包" == action:
            self.openBackpack()

    def followDetection(self):
        """
        跟随检测函数

        该函数用于检测并执行队伍跟随操作，主要流程包括：
        1. 打开队伍界面
        2. 检查一键召回按钮是否存在
        3. 如果存在则执行召回操作并等待

        无参数

        无返回值
        """
        self.openTeam()
        # 检查一键召回按钮是否存在，如果不存在则直接返回
        if not self.exits("按钮队伍一键召回"):
            self.closeTeam()
            return
        self.logs("召回队员")
        self.touch("按钮队伍一键召回")
        self.closeTeam()
        # 延迟20秒等待操作完成
        self.defer(20)

    def useBackpackArticles(self, articles, UsageTimes):
        """
        使用背包中的指定道具

        参数:
            articles (str): 要使用的道具名称
            UsageTimes (int): 使用次数

        返回值:
            bool: 如果道具不存在返回False，否则无返回值(None)
        """
        self.openBackpack()
        self.touch("按钮搜索")
        self.touch("标志输入道具名称")
        self.input(text=articles)
        self.touch("按钮搜索")

        # 检查道具是否存在，如果不存在则返回False
        if self.exits(f"标志物品{articles}"):
            # 循环使用指定次数的道具
            for _ in range(UsageTimes):
                self.touch(f"标志物品{articles}")
                self.touch("按钮背包使用")
            self.closeBackpack()
            return True
        self.logs(f"道具{articles}不存在")
        self.closeBackpack()
        return False

    def exchange(self, **kwargs):
        """查找文字"""

        def __exites():
            """内部判断方法"""
            for index in range(len(args)):
                x = 0 if index == 0 else 5 if digits[0] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] else 0
                if not self.exits(
                        args[index],
                        box=(
                                result[0] + 25 * index - 13 - x,
                                result[1] - 13,
                                result[0] + 25 * index + 13 - x,
                                result[1] + 13
                        )
                ):
                    return False
            return True

        text = kwargs.get("text", "")
        digits = [d for d in str(text)]
        args = [f"标志{i}" for i in digits]
        for result in self.exits(args[0], find_all=True):
            if __exites():
                self.click_mouse(pos=(result[0], result[1]))
                return True
        return False

    def switchBranchLine(self, index):
        """
        切换游戏副本的分线

        参数:
            index (int): 目标分线的索引号

        返回值:
            None
        """
        self.logs(f"切换分线{index}")
        digits = [int(d) for d in str(index)]
        args = [f"标志{i}" for i in digits]

        self.click_mouse(pos=(1230, 25))
        # 循环滑动屏幕查找目标分线按钮，每次向上滑动一定距离

        for _ in range(index // 7 + 5):
            results = self.exits("标志线", find_all=True)
            for result in results:
                if len(digits) == 1:
                    if self.exits(args[0], box=(result[0] - 35, result[1] - 20, result[0] - 15, result[1] + 20)):
                        self.click_mouse(pos=(result[0] - 30, result[1]))
                        return
                if len(digits) == 2:
                    if self.exits(args[0],
                                  box=(result[0] - 50, result[1] - 20, result[0] - 30, result[1] + 20)) and self.exits(
                            args[1], box=(result[0] - 35, result[1] - 20, result[0] - 15, result[1] + 20)):
                        self.click_mouse(pos=(result[0] - 50, result[1]))
                        return
            self.move_mouse(start=(1050, 555), end=(1050, 355))

        self.click_mouse(pos=(1335, 750))

    def unstuck(self):
        """
        执行脱离卡死操作的函数

        该函数通过一系列操作来解决程序卡死的问题，包括返回主界面、
        模拟按键、打开设置、执行特定设置操作等步骤。

        参数:
            无

        返回值:
            无
        """
        self.logs("脱离卡死")
        # 模拟空格键点击
        self.keepAlive()
        # 返回主界面操作
        self.backToMain(exclude_branches=["副本退出"])
        # 打开设置界面
        self.openSetting()
        # 点击设置界面中的脱离卡死按钮
        self.touch("按钮设置脱离卡死")
        # 点击设置界面中的确定按钮
        self.touch("按钮设置确定")
        self.defer(count=5)
        # 关闭设置界面
        self.closeSetting()

    def autoFight(self):
        """
        自动战斗循环函数，在后台线程中执行按键操作
        该函数会持续循环执行，直到autoFightEvent事件被设置为止
        循环中会按照taskConfig中配置的按键列表依次执行按键点击操作
        """
        __queue = deque([0, 1, 2, 3, 4, 5, 6, 7, 13])

        while not self.autoFightEvent.is_set():
            index = __queue.popleft()
            __queue.append(index)
            self.click_key(key=self.taskConfig.keyList[index])

    def autoFightStop(self):
        """
        停止自动战斗功能
        通过设置autoFightEvent事件来通知自动战斗循环停止执行
        """
        self.logs("停止自动战斗")
        self.autoFightEvent.set()

    def autoFightStart(self):
        """
        启动自动战斗功能
        清除autoFightEvent事件并创建新的后台线程来执行自动战斗循环
        """
        self.logs("启动自动战斗")
        # 清除停止事件，确保自动战斗可以正常开始
        self.autoFightEvent.clear()
        # 创建并启动自动战斗的后台线程
        threading.Thread(target=self.autoFight, daemon=True).start()

    def worldShouts(self, text, ordinary=True, connected=False):
        # 返回主界面并点击世界聊天入口
        self.backToMain()
        self.click_mouse(pos=(305, 600))

        # 检查普通世界按钮是否存在，如果存在且允许在普通世界发送则执行发送操作
        if ordinary:
            self.touch("按钮大世界普通世界", "按钮大世界普通世界_V1", box=(0, 0, 150, 750))
            self.touch("标志点击输入文字")
            self.input(text=text)
            self.touch("按钮大世界发送")

        if connected:
            self.touch("按钮大世界互联世界", box=(0, 0, 150, 750))
            self.touch("标志点击输入文字")
            self.input(text=text)
            self.touch("按钮大世界发送")

        # 退出聊天界面
        self.touch("按钮聊天退出")

    def activatedTask(self, *args, model):
        """
        激活江湖任务栏功能

        参数:
            *args: 可变参数，传递给touch方法的额外参数

        返回值:
            无返回值
        """
        self.backToMain(exclude_branches=["副本退出"])
        if model == "江湖":
            self.logs("激活江湖栏")
            # 检查任务栏是否已经激活
            if self.exits("按钮主界面江湖-激活"):
                self.move_mouse(start=(118, 300), end=(118, 452))
                return self.touch(*args, threshold=0.8)
            # 检查任务图标是否激活，如果激活则点击江湖按钮
            if self.exits("按钮主界面任务图标-激活"):
                self.touch("按钮主界面江湖-未激活")
                return self.touch(*args, threshold=0.8)
            # 任务图标未激活时的处理流程
            self.touch("按钮主界面任务图标-未激活")
            self.touch("按钮主界面江湖-未激活")
            self.move_mouse(start=(118, 300), end=(118, 452))
            return self.touch(*args, threshold=0.8)
        if model == "任务":
            self.logs("激活任务栏")
            # 检查任务栏是否已经激活
            if self.exits("按钮主界面任务-激活"):
                return self.touch(*args, threshold=0.8)
            # 检查任务图标是否激活，如果激活则点击江湖按钮
            if self.exits("按钮主界面任务图标-激活"):
                self.touch("按钮主界面任务-未激活")
                return self.touch(*args, threshold=0.8)
            # 任务图标未激活时的处理流程
            self.touch("按钮主界面任务图标-未激活")
            self.touch("按钮主界面任务-未激活")
            self.move_mouse(start=(118, 300), end=(118, 452))
            return self.touch(*args, threshold=0.8)
        return None

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
        while not self._finished.is_set():
            # 限制循环次数，防止无限等待
            if __count > 3:
                break
            # 检查是否正在加载地图，如果是则继续等待
            if self.exits("标志地图加载", "标志地图加载_V1"):
                __count = 0
                continue
            __count += 1
            time.sleep(1)
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
        self.areaGo("金陵", exits=True, unstuck=True)

    def areaGo(self, area, x=None, y=None, exits=False, unstuck=False, area_switch=True):
        """
        前往指定区域

        :param exits: 是否检测当前区域
        :param unstuck: 执行前是否脱离卡死
        :param area_switch: 当前区域前往
        :param area: 目标区域名称
        :param x: 目标区域的x坐标，如果为None则使用默认坐标
        :param y: 目标区域的y坐标，如果为None则使用默认坐标
        :return: 无返回值
        """
        __coordinate = {
            "金陵": (571, 484),
            "江南": (1095, 1117),
            "风雷岛": (970, 542),
            "中原": (1080, 996),
            "塞北": (1277, 718),
            "华山": (344, 206),
            "少林": (239, 326),
        }

        # 如果未指定坐标，则使用默认坐标
        x = __coordinate[area][0] if x is None else x
        y = __coordinate[area][1] if y is None else y

        # 是否脱离卡死
        if unstuck:
            self.unstuck()

        self.logs(f"{area}区域坐标前往 {x}:{y}")
        self.openMap()

        # 检查是否已经处于目标区域
        if exits and self.exits(f"标志地图{area}坐标", box=(125, 660, 300, 750)):
            self.logs(f"当前已处于{area}区域")
            self.closeMap()
            return

        # 执行前往区域的操作流程
        if area_switch:
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
        self.input(text=x)

        # 输入纵坐标值
        self.touch("按钮地图纵坐标")
        self.input(text=y)

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
        if not self.exits("标志队伍未创建"):
            self.touch("按钮队伍退出")
            self.touch("按钮队伍确定")
        self.closeTeam()

    def teamCreate(self, model):
        self.logs(f"创建{model}队伍")

        def __team_1():
            self.logs("刷新当天日常")
            self.openBackpack()
            self.touch("按钮物品综合入口")
            self.touch("按钮物品活动")
            self.touch("按钮活动江湖")
            self.touch("按钮活动江湖纪事", y=45)
            self.backToMain()
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍江湖纪事")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        def __team_2():
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍行当玩法")
            self.touch("按钮队伍江湖行商")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        def __team_3():
            self.openTeam()
            self.touch("按钮队伍创建")
            self.touch("按钮队伍下拉")
            self.move_mouse(start=(258, 307), end=(258, 607))
            self.touch("按钮队伍无目标")
            self.touch("按钮队伍行当玩法")
            self.touch("按钮队伍聚义平冤")
            self.touch("按钮队伍确定", x=-100)
            self.touch("按钮队伍确定")
            self.touch("按钮队伍确定")
            self.closeTeam()

        _dict = {
            "日常": __team_1,
            "江湖行商": __team_2,
            "聚义平冤": __team_3
        }

        _dict[model]()

    def buy(self, model):
        """
        执行购买操作

        :param model: 购买模式，可选值为"摆摊购买"或"商城购买"或"帮派仓库"
        :return: 无返回值
        """
        if model == "摆摊购买":

            # 检查交易界面是否存在
            if not self.exits("界面交易"):
                return False

            self.logs("摆摊购买")

            # 点击交易需求按钮并执行购买流程
            self.touch("按钮交易需求", x=130, y=35)
            if self.touch("按钮交易购买"):
                self.touch("按钮交易确定")

            self.touch("按钮交易查看全服", seconds=None)

            self.closeStalls()
            self.defer(3)
            return True

        if model == "商城购买":
            # 检查商城界面是否存在
            if not self.exits("界面珍宝阁"):
                return False
            # 记录商城购买日志并执行购买操作
            self.logs("商城购买")
            self.click_mouse(pos=(990, 690), count=8)

            # 关闭商城界面
            self.closeMall()
            self.defer(3)
            return True

        if model == "帮派仓库":
            if not self.exits("界面帮派仓库"):
                return False
            self.logs("帮派仓库提交")
            self.touch("按钮帮派仓库提交")
            self.closeBanStore()
            self.defer(count=3)

            return True
        return False

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
        # 循环执行关闭操作，直到达到指定次数或无法找到关闭按钮
        for i in range(count):
            results = self.exits("按钮关闭", "按钮关闭_V1", "按钮关闭_V2", "按钮关闭_V3", box=box, find_all=True)
            if not results:
                continue
            self.click_mouse(pos=results, click_mode="last", post_delay=0)

    def backToMain(self, exclude_branches=None):
        """
        返回主界面函数

        该函数用于从当前界面返回到主界面，通过不断关闭当前UI直到检测到主界面按钮

        参数:
            self: 类实例本身

        返回值:
            无返回值
        """
        self.logs("返回主界面")
        exclude = exclude_branches or []
        _count = 0
        # 循环关闭当前界面直到返回主界面或任务完成
        while not self._finished.is_set():
            # 副本退出分支（可屏蔽）
            if "副本退出" not in exclude and self.exits("按钮副本退出"):
                self.touch("按钮副本退出")
                self.touch("按钮回到坊间", "按钮确定", "按钮离开")
                continue

            # 物品界面关闭分支（可屏蔽）
            if "物品界面" not in exclude and self.exits("界面物品"):
                self.click_mouse(pos=(0, 0))

            # 购买确认关闭分支（可屏蔽）
            if "购买确认" not in exclude and self.exits("标志购买确认"):
                self.touch("按钮取消")

            # 聊天窗口关闭分支（可屏蔽）
            if "聊天窗口" not in exclude and self.exits("按钮聊天退出"):
                self.touch("按钮聊天退出")

            # 检查是否已经回到主界面
            if self.exits("按钮世界挂机"):
                _count += 1
                if _count >= 3:
                    break
                continue
            _count = 0

            self.closeCurrentUi()
            self.keepAlive()

    def closeDreamCub(self):
        """
        关闭梦崽界面

        该函数用于关闭当前打开的梦崽界面。如果当前不在梦崽界面，则直接返回。

        参数:
            无

        返回值:
            无
        """

        # 检查当前是否已处于梦崽界面，如果不是则直接返回
        if not self.exits("标志限时礼包"):
            return
        self.logs("关闭梦崽礼包")
        # 关闭当前用户界面
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

        # 检查帮派仓库界面是否存在，不存在则直接返回
        if not self.exits("界面帮派仓库"):
            return
        self.logs("关闭帮派仓库")
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

        # 检查交易界面是否存在，如果不存在则直接返回
        if not self.exits("界面交易"):
            return
        self.logs("关闭摆摊")
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

        # 检查珍宝阁界面是否存在，不存在则直接返回
        if not self.exits("界面珍宝阁"):
            return
        self.logs("关闭珍宝阁")
        # 执行关闭当前界面的操作
        self.closeCurrentUi()

    def closeExchangeShop(self):
        """关闭兑换商店"""
        if not self.exits("界面兑换商店"):
            return
        self.logs("关闭兑换商店")
        self.closeCurrentUi()

    def openExchangeShop(self):
        """打开兑换商店"""
        if self.exits("界面兑换商店"):
            return
        self.logs("打开兑换商店")
        self.openBackpack()
        self.touch("按钮物品积分")
        self.touch("按钮物品打开兑换商店")

    def closeFlyingEagle(self):
        """关闭飞鹰界面"""
        if not self.exits("界面飞鹰"):
            return
        self.logs("关闭飞鹰")
        self.closeCurrentUi()

    def openFlyingEagle(self):
        """打开飞鹰界面"""
        if self.exits("界面飞鹰"):
            return
        self.logs("打开飞鹰")
        self.openBuddy()
        self.touch("按钮好友飞鹰")

    def closeFaction(self):
        """
        关闭帮派界面

        该函数用于关闭当前打开的帮派界面。如果当前不在帮派界面，则直接返回。

        参数:
            无

        返回值:
            无
        """

        # 检查当前是否已处于帮派界面，如果不是则直接返回
        if not self.exits("界面帮派"):
            return
        self.logs("关闭帮派")
        self.closeCurrentUi()

    def openFaction(self):
        """
        打开帮派界面功能函数

        该函数用于打开游戏中的帮派界面，首先会检查帮派界面是否已经存在，
        如果不存在则通过按键操作来打开界面。

        参数:
            无

        返回值:
            无
        """

        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if not self.exits("界面帮派"):
            self.logs("打开帮派")
            self.click_key(key=self.taskConfig.keyList[21])

    def closeBuddy(self):
        """
        关闭好友界面功能函数

        该函数用于关闭当前打开的好友界面，如果当前不在好友界面则不执行任何操作

        参数:
            self: 类实例本身

        返回值:
            无返回值
        """

        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("界面好友"):
            return
        self.logs("关闭好友")
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

        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if not self.exits("界面好友"):
            self.logs("打开好友")
            self.click_key(key=self.taskConfig.keyList[24])

    def closeMap(self):
        """
        关闭地图界面

        该函数用于关闭当前打开的地图界面

        Returns:
            None
        """

        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("标志地图当前坐标"):
            return
        self.logs("关闭地图")
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

        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if not self.exits("标志地图当前坐标"):
            self.logs("打开地图")
            self.click_key(key=self.taskConfig.keyList[23])

    def closeTeam(self):
        """
        关闭队伍界面

        该函数用于关闭当前打开的队伍界面

        参数:
            无

        返回值:
            无
        """
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("界面队伍"):
            return
        self.logs("关闭队伍")
        self.closeCurrentUi()
        self.defer(count=2)

    def openTeam(self):
        """
        打开队伍界面函数

        该函数用于打开游戏中的队伍界面，如果队伍界面未开启则通过按键T来打开
        """
        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if not self.exits("界面队伍"):
            self.logs("打开队伍")
            self.click_key(key=self.taskConfig.keyList[22])

    def closeBackpack(self):
        """
        关闭背包界面

        该函数用于关闭当前打开的背包界面

        Returns:
            无返回值
        """
        self.logs("关闭背包")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("界面物品"):
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
        if not self.exits("界面物品"):
            self.click_key(key=self.taskConfig.keyList[20])

    def closeSetting(self):
        """
        关闭设置界面

        该函数用于关闭当前打开的设置界面。如果当前不在设置界面，
        则直接返回；如果在设置界面，则执行关闭操作。

        Returns:
            None
        """
        self.logs("关闭设置")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("界面设置"):
            return
        self.closeCurrentUi()

    def openSetting(self):
        """
        打开游戏设置界面

        该函数通过按键操作打开游戏的设置界面。如果当前不在设置界面，
        会先按ESC键打开主菜单，然后进入设置界面。

        参数:
            self: 类实例本身

        返回值:
            无
        """
        self.logs("打开设置")
        # 检查当前是否已处于物品界面，如果不是则按键打开背包
        if not self.exits("界面设置"):
            self.click_key(key=self.taskConfig.keyList[25])

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
        __start = time.time()
        self.logs("等待寻路结束")
        while not self._finished.is_set():
            # 检查是否正在寻路中，如果是则继续等待
            # 检查是否正在加载地图，如果是则继续等待
            if self.exits("标志寻路中") or self.exits("标志地图加载", "标志地图加载_V1"):
                __count = 0
                continue
            if time.time() - __start > 360:
                self.logs("寻路超时")
                __start = time.time()
                self.unstuck()
                self.touch("按钮继续寻路")
            # 限制循环次数，防止无限等待
            if __count > 3:
                break
            __count += 1
            time.sleep(1)
        self.logs("寻路结束")

    def switchCharacter(self):
        """
        切换游戏角色

        该函数用于执行角色切换操作，包括打开设置、点击切换角色按钮、
        确认切换并等待进入游戏界面

        参数:
            无

        返回值:
            无
        """
        self.backToMain()
        self.openSetting()
        self.touch("按钮设置切换角色")
        self.touch("按钮设置确定")
        # 等待登录进入游戏按钮出现，超时时间30秒
        self.wait("按钮登录进入游戏", seconds=30)

    def switchCharacterOne(self):
        """
        切换第一个角色并进入游戏

        该函数执行以下操作：
        1. 调用切换角色方法
        2. 点击指定坐标位置
        3. 触摸登录按钮进入游戏
        4. 延迟等待游戏加载
        5. 设置角色信息

        无参数

        无返回值
        """
        self.logs("切换角色一")
        self.switchCharacter()
        self.click_mouse(pos=(1245, 70))
        self.touch("按钮登录进入游戏")
        self.defer(count=30)
        self.setCharacterInfo()

    def switchCharacterTwo(self):
        """
        切换到第二个角色并进入游戏

        该函数执行以下操作：
        1. 调用切换角色方法
        2. 点击屏幕指定坐标位置
        3. 触摸登录按钮进入游戏
        4. 延迟等待游戏加载
        5. 设置角色信息

        无参数

        无返回值
        """
        self.logs("切换角色二")
        self.switchCharacter()
        self.click_mouse(pos=(1245, 170))
        self.touch("按钮登录进入游戏")
        self.defer(count=30)
        self.setCharacterInfo()

    def switchCharacterThree(self):
        """
        切换第三个角色并进入游戏

        该函数执行以下操作：
        1. 调用切换角色方法
        2. 点击指定坐标位置
        3. 触摸登录按钮进入游戏
        4. 延迟等待游戏加载
        5. 设置角色信息

        无参数

        无返回值
        """
        self.logs("切换角色三")
        self.switchCharacter()
        self.click_mouse(pos=(1245, 270))
        self.touch("按钮登录进入游戏")
        self.defer(count=30)
        self.setCharacterInfo()

    def switchCharacterFour(self):
        """
        切换到第四个角色并进入游戏

        该函数执行以下操作：
        1. 调用切换角色方法
        2. 点击指定坐标位置
        3. 触摸登录按钮进入游戏
        4. 延迟等待30秒
        5. 设置角色信息

        无参数

        无返回值
        """
        self.logs("切换角色四")
        self.switchCharacter()
        self.click_mouse(pos=(1245, 370))
        self.touch("按钮登录进入游戏")
        self.defer(count=30)
        self.setCharacterInfo()

    def switchCharacterFive(self):
        """
        切换到第五个角色并进入游戏

        该函数执行以下操作：
        1. 调用切换角色方法
        2. 点击屏幕指定坐标位置
        3. 触摸登录按钮进入游戏
        4. 延迟等待30秒
        5. 设置角色信息

        无参数

        无返回值
        """
        self.logs("切换角色五")
        self.switchCharacter()
        self.click_mouse(pos=(1245, 470))
        self.touch("按钮登录进入游戏")
        self.defer(count=30)
        self.setCharacterInfo()

    def switchCharacterDefault(self):
        """
        切换角色默认设置

        该函数用于切换当前角色的默认配置信息

        参数:
            self: 类实例本身

        返回值:
            无
        """
        self.setCharacterInfo()

    def setCharacterInfo(self):
        """
        设置并发送角色信息到前端界面

        该函数通过以下步骤获取角色信息：
        1. 返回游戏主界面
        2. 打开背包界面
        3. 点击物品属性按钮
        4. 截取角色信息区域图像
        5. 将图像转换为base64编码并发送到前端

        参数:
            无

        返回值:
            无
        """
        self.logs("设置角色信息")
        self.backToMain(exclude_branches=["副本退出"])
        self.openBackpack()
        self.touch("按钮物品属性")
        self.defer(count=3)
        # 截取角色信息区域并转换图像格式
        character = pil_2_cv2(self.winConsole.capture.crop((742, 158, 892, 186)))

        # 将图像编码为PNG格式的二进制数据
        _, buffer = cv2.imencode('.png', character)

        # 将图像数据转换为base64编码并发送到前端界面
        self.queueListener.emit(
            {
                "event": "JS:EMIT",
                "args": (
                    "API:UPDATE:CHARACTER",
                    {
                        "character": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}",
                        "hwnd": self.hwnd
                    }
                )
            }
        )
        self.backToMain(exclude_branches=["副本退出"])
