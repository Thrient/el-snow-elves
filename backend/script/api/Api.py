class Api:
    def __init__(self):
        self._events = {}

    def on(self, event, callback):
        """注册事件监听器"""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)
        return self

    def off(self, event, callback=None):
        """移除事件监听器"""
        if event in self._events:
            if callback is None:
                del self._events[event]
            else:
                if callback in self._events[event]:
                    self._events[event].remove(callback)

    def emit(self, event, *args):
        """触发事件"""
        if event not in self._events:
            return None

        if len(self._events[event]) == 1:
            return self._events[event][0](*args)

        for callback in self._events[event]:
            callback(*args)
        return None


# 创建全局Api实例
api = Api()