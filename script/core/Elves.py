import logging
import multiprocessing as mp
import os

import webview

from script.config.Config import Config
from script.core.HotkeyManager import hot_key_manager
from script.core.Script import Script
from script.core.Url import Url
from script.functools.functools import delay
from script.utils.Api import api
from script.utils.JsApi import js
from script.utils.QueueListener import QueueListener
from script.utils.TaskConfig import TaskConfig
from script.utils.Utils import Utils

logger = logging.getLogger(__name__)


class Elves:
    def __init__(self, url):
        self.window = webview.create_window(
            '时雪',
            Url(primary_url=url, txt_url=None).find_best_url_by_latency(),
            js_api=api,
            confirm_close=True,
            width=1335,
            height=750
        )
        self.js = js
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
        # === 1. 生命周期控制（核心） ===
        api.on("API:SCRIPT:BIND", self.bind)
        api.on("API:SCRIPT:SEARCH", self.search)
        api.on("API:SCRIPT:START", self.start)
        api.on("API:SCRIPT:END", self.end)
        api.on("API:SCRIPT:UNBIND", self.unbind)

        # 注册脚本版本监听器
        api.on("API:SCRIPT:VERSION", lambda: Config.VERSION)
        # 注册脚本更新事件监听器
        api.on("API:SCRIPT:UPDATE", self.update)
        # 注册脚本启动事件监听器
        api.on("API:SCRIPT:START", self.start)

        api.on("API:SCRIPT:STOP", self.stop)
        # 注册脚本恢复事件监听器
        api.on("API:SCRIPT:RESUME", self.resume)
        # 注册脚本全屏监听器
        api.on("API:SCRIPT:FULLSCREEN", self.fullScreen)
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
        api.on("API:TASK:CONFIG:EXECUTE:LIST", TaskConfig.getConfigExecuteList)

        hot_key_manager.register("ctrl+shift+e", self.hot_key_bind, "快捷键启动")

        self.window.events.closed += self.on_closed

        self.js.init(self.window)

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
        for script, queueListener in self.winList.values():
            # 调用脚本对象的解绑方法
            queueListener.emit(
                {
                    "event": "API:SCRIPT:UNBIND",
                    "args": (

                    )
                }
            )

            queueListener.terminate()

        hot_key_manager.stop()

    def update(self):
        """更新"""
        self.window.destroy()

        current_dir = os.getcwd()

        # 拼接bat脚本的完整路径（替换为你的bat文件名）
        path = os.path.join(current_dir, "Update.exe")

        os.system(path)

    def unbind(self, hwnd):
        """解绑"""
        # 检查窗口句柄是否存在于窗口列表中
        if hwnd not in self.winList:
            return
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:UNBIND",
                "args": (

                )
            }
        )

        queueListener.terminate()

        # 从窗口列表中删除该窗口句柄对应的项
        del self.winList[hwnd]

    def stop(self, hwnd):
        """停止指定窗口"""
        # 检查窗口是否在窗口列表中
        if hwnd not in self.winList:
            return
        # 获取窗口对应的脚本并停止执行
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:STOP",
                "args": (

                )
            }
        )

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
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:RESUME",
                "args": (

                )
            }
        )

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
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:LOCK",
                "args": (

                )
            }
        )

    def fullScreen(self, hwnd):
        if hwnd not in self.winList:
            return
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:FULLSCREEN",
                "args": (

                )
            }
        )

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
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:UNLOCK",
                "args": (

                )
            }
        )

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
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:TRANSPARENT",
                "args": (
                    transparent,
                )
            }
        )

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
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:SCREENSHOT",
                "args": (

                )
            }
        )

    def search(self):
        """

        :return:
        """

        for hwnd in Utils.getHwndByTitle():

            if hwnd in self.winList:
                continue
            self.launch_script(hwnd)

    def launch_script(self, hwnd):
        queue = mp.Queue()
        queueListener = QueueListener(queue, hwnd, "elves")

        script = Script(hwnd=hwnd, queue=queue)
        Utils.sendEmit(self.window, 'API:CHARACTERS:ADD', state='初始化', hwnd=hwnd, config="当前配置")
        self.winList[hwnd] = [script, queueListener]

        # 启动监听器
        queueListener.start()
        # 运行脚本
        script.start()

    def end(self, hwnd):
        # 如果该窗口已在监控列表中，则直接返回
        if hwnd not in self.winList:
            return

        # 创建新的脚本实例并添加到窗口列表中
        script, queueListener = self.winList.get(hwnd)

        queueListener.emit(
            {
                "event": "API:SCRIPT:END",
                "args": (

                )
            }
        )

    def start(self, hwnd, config, task, parameter):
        """启动"""

        # 如果该窗口不在监控列表中，则直接返回
        if hwnd not in self.winList:
            return

        # 创建新的脚本实例并添加到窗口列表中
        script, queueListener = self.winList[hwnd]

        # 通过队列向子进程发送启动命令
        queueListener.emit(
            {
                'event': 'API:SCRIPT:LAUNCH',
                'args': (
                    config,
                    task,
                    parameter
                )
            }
        )

    @delay(pre_delay=2000)
    def bind(self, config):
        """绑定"""
        hwnd = Utils.getHwndByMouseAndTitle()

        if hwnd in self.winList:
            return

        self.launch_script(hwnd=hwnd)

        self.start(hwnd, "当前配置", "", **config)

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
        webview.start(
            private_mode=False,
            storage_path=Config.STORAGE_PATH,
            debug=debug
        )
