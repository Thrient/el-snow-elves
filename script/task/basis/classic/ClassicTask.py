import base64
import threading
import time
from abc import ABC
from collections import deque
from threading import Event

import cv2
from airtest.aircv.utils import pil_2_cv2

from script.task.basis.classic.ClassicBackpackTask import ClassicBackpackTask
from script.task.basis.classic.ClassicInstanceTask import ClassicInstanceTask
from script.task.basis.classic.ClassicMapTask import ClassicMapTask
from script.task.basis.classic.ClassicTeamTask import ClassicTeamTask
from script.utils.Thread import thread


class ClassicTask(ClassicTeamTask, ClassicInstanceTask, ClassicBackpackTask, ClassicMapTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动战斗
        self.autoFightEvent = Event()
        self.popCheck()

    @thread(daemon=True)
    def popCheck(self):
        while not self._finished.is_set():
            self.closeDreamCub()

            if self.exits("界面特惠"):
                self.closeCurrentUi()

            if self.exits("标志副本提示"):
                self.touch("按钮取消")

            if self.exits("标志特殊弹窗_V1", "标志特殊弹窗_V2"):
                self.touch("按钮确定")

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
        self.backToMain()
        self.click_mouse(pos=(1330, 715))
        self.touch("按钮大世界镜头重置")
        self.click_mouse(pos=(1330, 715))

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
        self.backToMain()
        # 打开设置界面
        self.openSetting()
        # 点击设置界面中的脱离卡死按钮
        self.touch("按钮设置脱离卡死")
        # 点击设置界面中的确定按钮
        self.touch("按钮设置确定")
        self.defer(count=5)
        # 关闭设置界面
        self.closeSetting()

    def exitInstance(self):
        """退出场景"""
        while not self._finished.is_set():
            self.backToMain()
            if not self.exits("按钮副本退出", "按钮副本退出_V1"):
                return
            self.logs("退出副本场景")
            self.touch("按钮副本退出", "按钮副本退出_V1")
            self.touch("按钮回到坊间", "按钮确定", "按钮离开")

    def autoFight(self):
        """
        自动战斗循环函数，在后台线程中执行按键操作
        该函数会持续循环执行，直到autoFightEvent事件被设置为止
        循环中会按照taskConfig中配置的按键列表依次执行按键点击操作
        """
        __queue = deque([0, 1, 2, 3, 4, 5, 6, 7, 12, 13])

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

    def activatedTask(self, *args, model):
        """
        激活江湖任务栏功能

        参数:
            *args: 可变参数，传递给touch方法的额外参数

        返回值:
            无返回值
        """
        self.backToMain()
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
        return []

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
        """位置检测函数"""
        self.logs("位置检测")
        self.exitInstance()
        # self.areaGo("金陵", exits=True, unstuck=True)

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

    def openActivity(self):
        """打开活动"""
        if self.exits("界面活动"):
            return
        self.openBackpack()
        self.touch("按钮物品综合入口")
        self.logs("打开活动")
        self.touch("按钮物品活动")

    def openBounty(self):
        if self.exits("界面悬赏"):
            return
        self.backToMain()
        self.openActivity()
        self.logs("打开悬赏")
        self.touch("按钮活动悬赏")

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
                break
            # 限制循环次数，防止无限等待
            if __count > 6:
                break
            __count += 1
            time.sleep(1)
        self.logs("寻路结束")

    def ordinary_shout(self, text):
        self.backToMain()
        self.click_mouse(pos=(305, 600))
        self.touch("按钮大世界普通世界", "按钮大世界普通世界_V1", box=(0, 0, 150, 750))
        self.touch("标志点击输入文字")
        self.input(text=text)
        self.touch("按钮大世界发送")
        self.touch("按钮聊天退出")

    def connect_shout(self, text):
        self.backToMain()
        self.click_mouse(pos=(305, 600))
        self.touch("按钮大世界互联世界", box=(0, 0, 150, 750))
        self.touch("标志点击输入文字")
        self.input(text=text)
        self.touch("按钮大世界发送")
        self.touch("按钮聊天退出")

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
        self.backToMain()
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
                    "API:CHARACTERS:UPDATE",
                    {
                        "character": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}",
                        "hwnd": self.hwnd
                    }
                )
            }
        )
        self.backToMain()
