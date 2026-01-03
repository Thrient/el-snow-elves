from script.utils.Api import api
from script.utils.Utils import Utils


class JsApi:
    def __init__(self):
        self.window = None

    def init(self, window):
        """初始化"""
        self.window = window

    def emit(self, event, kwargs):
        """发送信息"""
        Utils.sendEmit(self.window, event=event, callback=self.callback, **kwargs)

    @staticmethod
    def callback(data):
        """回调函数"""
        pass


js = JsApi()
