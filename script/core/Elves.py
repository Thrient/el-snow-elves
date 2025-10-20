import os
import time

import webview

from script.config.Config import Config
from script.core.HotkeyManager import hot_key_manager
from script.core.Script import Script
from script.utils.Api import api
from script.utils.TaskConfig import TaskConfig
from script.utils.Utils import Utils


class Elves:
    def __init__(self, url='dist/index.html'):
        self.window = webview.create_window('时雪', url=url, js_api=api, confirm_close=True, width=1335, height=750)
        self.winList = {}
        self.init()

    def init(self):
        """
        初始化脚本事件监听器

        该函数用于注册脚本运行所需的各种事件回调函数，包括启动、解绑、停止和恢复事件。
        通过api.on方法将对应的事件标识符与处理函数进行绑定。

        参数:
            self: 类实例引用

        返回值:
            无
        """
        # 注册脚本更新事件监听器
        api.on("API:SCRIPT:UPDATE", self.update)
        # 注册脚本启动事件监听器
        api.on("API:SCRIPT:START", self.start)
        # 注册脚本结束事件监听器
        api.on("API:SCRIPT:END", self.end)
        # 注册脚本查找事件监听器
        api.on("API:SCRIPT:SEARCH", self.search)
        # 注册脚本绑定监听器
        api.on("API:SCRIPT:BIND", self.bind)
        # 注册脚本解绑事件监听器
        api.on("API:SCRIPT:UNBIND", self.unbind)
        # 注册脚本停止事件监听器
        api.on("API:SCRIPT:STOP", self.stop)
        # 注册脚本恢复事件监听器
        api.on("API:SCRIPT:RESUME", self.resume)
        # 注册窗口锁定事件监听器
        api.on("API:SCRIPT:LOCK", self.lock)
        # 注册窗口解锁事件监听器
        api.on("API:SCRIPT:UNLOCK", self.unlock)
        # 注册设置窗口透明度事件监听器
        api.on("API:SCRIPT:SET_TRANSPARENT", self.setTransparent)
        # 注册脚本截图事件监听器
        api.on("API:SCRIPT:SCREENSHOT", self.screenshot)
        # 注册配置保存事件处理函数
        api.on("API:TASK:CONFIG:SAVE", TaskConfig.saveConfig)

        api.on("API:TASK:CONFIG:DELETE", TaskConfig.deleteConfig)
        # 注册任务配置加载事件处理函数
        api.on("API:TASK:CONFIG:lOAD", TaskConfig.loadConfigDict)
        # 注册配置列表获取事件处理函数
        api.on("API:TASK:CONFIG:LIST", TaskConfig.getTaskList)


        hot_key_manager.register("ctrl+shift+e", self.hot_key_bind, "快捷键启动")

        self.window.events.closed += self.on_closed

    def on_closed(self):
        """
        窗口关闭时的回调函数

        该函数在窗口关闭时被调用，用于清理相关的脚本资源。
        遍历所有窗口列表中的脚本对象，并调用它们的解绑方法。

        参数:
            self: 类实例本身

        返回值:
            无
        """
        # 遍历所有脚本对象并执行解绑操作
        for script in self.winList.values():
            script.unbind()

        hot_key_manager.stop()

    #
    def update(self):
        self.window.destroy()

        current_dir = os.getcwd()

        # 拼接bat脚本的完整路径（替换为你的bat文件名）
        path = os.path.join(current_dir, "Update.exe")

        os.system(path)

    def unbind(self, hwnd):
        """
        解绑指定窗口句柄的脚本绑定

        参数:
            hwnd: 窗口句柄，用于标识要解绑的窗口

        返回值:
            无返回值
        """
        # 检查窗口句柄是否存在于窗口列表中
        if hwnd not in self.winList:
            return
        script = self.winList.get(hwnd)

        # 调用脚本对象的解绑方法
        script.unbind()

        # 从窗口列表中删除该窗口句柄对应的项
        del self.winList[hwnd]

        # 从配置中删除指定窗口句柄的角色切换状态记录
        del Config.SWITCH_CHARACTER_STATE[hwnd]

    def stop(self, hwnd):
        """
        停止指定窗口的脚本执行

        参数:
            hwnd: 窗口句柄，用于标识要停止脚本的窗口

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并停止执行
        script = self.winList.get(hwnd)
        script.stop()

    def resume(self, hwnd):
        """
        恢复指定窗口的脚本执行

        参数:
            hwnd: 窗口句柄，用于标识要恢复脚本的窗口

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并恢复执行
        script = self.winList.get(hwnd)
        script.resume()

    def lock(self, hwnd):
        """
        锁定指定窗口的脚本执行

        参数:
            hwnd: 窗口句柄，用于标识要锁定脚本的窗口

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并锁定执行
        script = self.winList.get(hwnd)
        script.lock()

    def unlock(self, hwnd):
        """
        解锁指定窗口的脚本执行

        参数:
            hwnd: 窗口句柄，用于标识要解锁脚本的窗口

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并解锁执行
        script = self.winList.get(hwnd)
        script.unlock()

    def setTransparent(self, hwnd, transparent):
        """
        设置指定窗口的透明度

        参数:
            hwnd: 窗口句柄，用于标识要设置透明度的窗口
            transparent: 透明度值，取值范围[0, 255]

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并设置透明度
        script = self.winList.get(hwnd)
        script.setTransparent(transparent)

    def screenshot(self, hwnd):
        """
        对指定窗口进行截图操作

        参数:
            hwnd: 窗口句柄，用于标识要截图的窗口

        返回值:
            无返回值
        """
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        script = self.winList.get(hwnd)
        script.screenshot()

    def search(self):
        """

        :return:
        """

        for hwnd in Utils.getHwndByTitle():

            if hwnd in self.winList:
                continue
            self.launch_script(hwnd)

    def launch_script(self, hwnd):
        script = Script(hwnd=hwnd, window=self.window)
        Utils.sendEmit(self.window, 'API:ADD:CHARACTER', state='初始化', hwnd=hwnd, config="默认配置")
        self.winList[hwnd] = script
        # 初始化窗口的切换角色状态
        Config.SWITCH_CHARACTER_STATE[hwnd] = [True, True, True, True, True, True]
        # 运行脚本
        script.start()

    def end(self, hwnd):
        # 如果该窗口已在监控列表中，则直接返回
        if hwnd not in self.winList:
            return

        # 创建新的脚本实例并添加到窗口列表中
        script = self.winList.get(hwnd)

        script.end()

    def start(self, hwnd, config):
        """
        启动脚本执行函数

        参数:
            **kwargs: 传递给任务配置的键值对参数

        返回值:
            无
        """

        # 如果该窗口不在监控列表中，则直接返回
        if hwnd not in self.winList:
            return

        # 创建新的脚本实例并添加到窗口列表中
        script = self.winList[hwnd]

        def callback(kwargs):
            script.switch_on(config=config, taskConfig=TaskConfig(**kwargs))

        Utils.sendEmit(self.window, 'API:TASK:CONFIG:GET', callback)

    def bind(self):
        """
        启动脚本执行函数

        参数:
            **kwargs: 传递给任务配置的键值对参数

        返回值:
            无
        """
        # 等待2秒后获取鼠标位置对应的窗口句柄
        time.sleep(2)
        hwnd = Utils.getHwndByMouseAndTitle()

        if hwnd in self.winList:
            return

        self.launch_script(hwnd=hwnd)

        self.start(hwnd, "默认配置")

    def hot_key_bind(self):
        """
        启动脚本执行函数

        参数:
            **kwargs: 传递给任务配置的键值对参数

        返回值:
            无
        """
        hwnd = Utils.getHwndByMouseAndTitle()

        if hwnd in self.winList:
            return

        self.launch_script(hwnd=hwnd)

        self.start(hwnd, "默认配置")

    @staticmethod
    def run(debug=False):
        """
        运行webview窗口应用程序

        该函数创建一个webview窗口并启动应用程序，加载指定的本地服务器地址
        并提供JavaScript API接口

        参数:

            self: 类实例引用

        返回值:
            无
        """
        # 启动webview应用程序
        # webview.start(http_server=True, ssl=True, private_mode=False, storage_path=Config.STORAGE_PATH)
        webview.start(http_server=True, ssl=True, private_mode=False, storage_path=Config.STORAGE_PATH, debug=debug)
