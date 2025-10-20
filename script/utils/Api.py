class Api:
    def __init__(self):
        self._events = {}

    def on(self, event, callback):
        """
        注册事件和回调函数
        :param event: 事件名称
        :param callback: 回调函数
        :return: None
        """
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)

    def off(self, event, callback=None):
        """
        取消注册事件
        :param event: 事件名称
        :param callback: 回调函数，如果为None则删除该事件的所有回调
        :return: None
        """
        if event in self._events:
            if callback is None:
                del self._events[event]
            else:
                if callback in self._events[event]:
                    self._events[event].remove(callback)

    def emit(self, event, *args):
        """
        触发事件
        :param event: 事件名称
        :param args: 回调函数的位置参数
        :return: None
        """
        if event in self._events:
            for callback in self._events[event]:
                # 如果有参数则传递，没有则不传递
                if args:
                    # 如果第一个参数是字典，则将其作为关键字参数传递
                    if len(args) == 1 and isinstance(args[0], dict):
                        return callback(**args[0])
                    else:
                        return callback(*args)
                else:
                    return callback()
        return None


api = Api()
