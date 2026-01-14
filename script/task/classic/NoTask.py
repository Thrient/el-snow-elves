import time

from script.task.basis.classic.ClassicTask import ClassicTask
from script.utils.Thread import thread


class NoTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup = "位置检测"
        # 事件变量字典
        self.event = {

        }
        # 状态-重置配置表：key=状态值，value=需要重置的变量
        self.state_reset_config = {

        }

    @thread(daemon=True)
    def popCheck(self):
        pass

    def execute(self):
        while not self._finished.is_set():

            match self.setup:
                case _:
                    time.sleep(1)
                    return 0
        return 0
