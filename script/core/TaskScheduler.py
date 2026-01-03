import queue

from script.core.TaskConfigScheduler import taskConfigScheduler


class TaskScheduler:

    def __init__(self, hwnd):
        self.counter = 0
        self.hwnd = hwnd
        self.queue = queue.PriorityQueue()

    def init(self, starter):
        self.clear()

        config = taskConfigScheduler.config[self.hwnd]["配置"]

        if len(config.switchCharacterList) == 0:
            self.add(0, "切换角色")
            if starter is not None:
                for task in [task["data"] for task in config.executeList][[task["data"] for task in config.executeList].index(starter):]:
                    self.add(0, task)
            else:
                for task in [task["data"] for task in config.executeList]:
                    self.add(0, task)

        else:
            for _ in config.switchCharacterList:
                self.add(0, "切换角色")
                for task in [task["data"] for task in config.executeList]:
                    self.add(0, task)

    def clear(self):
        self.queue = queue.PriorityQueue()

    def add(self, index, task):
        """
        向任务队列中添加新任务

        参数:
            index: 任务的优先级索引，用于确定任务执行顺序
            task: 要添加的任务对象

        返回值:
            无返回值

        功能说明:
            检查任务是否已存在，如果不存在则将任务添加到队列中
        """
        self.queue.put((index, self.counter, task))
        self.counter += 1

    def pop(self):
        if self.queue.empty():
            return None
        _, _, task = self.queue.get()
        return task

