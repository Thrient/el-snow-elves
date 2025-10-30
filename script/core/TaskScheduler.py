import queue
from threading import Event

from script.config.Config import Config
from script.core.TaskConfigScheduler import taskConfigScheduler


class TaskScheduler:

    def __init__(self, hwnd):
        self.counter = 0
        self.hwnd = hwnd
        self.queue = queue.PriorityQueue()
        self.tasks = set()

    def init(self):
        self.queue = queue.PriorityQueue()
        self.tasks.clear()
        self.counter = 0
        for task in taskConfigScheduler.read_common(self.hwnd).executeList:
            self.add(0, task["data"])

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
        # 只有当任务不存在时才进行添加操作
        if task not in self.tasks:
            self.queue.put((index, self.counter, task))
            self.tasks.add(task)
            self.counter += 1

    def pop(self):
        if not self.queue.empty():
            _, _, task = self.queue.get()
            self.tasks.remove(task)
            return task

        characterState = [
            "characterOne" in taskConfigScheduler.read_common(self.hwnd).switchCharacterList and
            Config.SWITCH_CHARACTER_STATE[self.hwnd][0],
            "characterTwo" in taskConfigScheduler.read_common(self.hwnd).switchCharacterList and
            Config.SWITCH_CHARACTER_STATE[self.hwnd][1],
            "characterThree" in taskConfigScheduler.read_common(self.hwnd).switchCharacterList and
            Config.SWITCH_CHARACTER_STATE[self.hwnd][2],
            "characterFour" in taskConfigScheduler.read_common(self.hwnd).switchCharacterList and
            Config.SWITCH_CHARACTER_STATE[self.hwnd][3],
            "characterFive" in taskConfigScheduler.read_common(self.hwnd).switchCharacterList and
            Config.SWITCH_CHARACTER_STATE[self.hwnd][4],
            all(Config.SWITCH_CHARACTER_STATE[self.hwnd])
        ]

        if any(characterState):
            self.init()
            return '切换角色'

        return None
