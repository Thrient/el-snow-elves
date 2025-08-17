import queue

from script.config.Config import Config


class TaskScheduler:

    def __init__(self, hwnd, taskConfig):
        self.counter = 0
        self.hwnd = hwnd
        self.taskConfig = taskConfig
        self.queue = queue.PriorityQueue()
        self.tasks = set()

    def init(self):
        self.queue = queue.PriorityQueue()
        self.tasks.clear()
        self.counter = 0
        for task in self.taskConfig.executeList:
            self.add(0, task["data"])

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
            self.taskConfig.switchCharacterOne and Config.SWITCH_CHARACTER_STATE[self.hwnd][0],
            self.taskConfig.switchCharacterTwo and Config.SWITCH_CHARACTER_STATE[self.hwnd][1],
            self.taskConfig.switchCharacterThree and Config.SWITCH_CHARACTER_STATE[self.hwnd][2],
            self.taskConfig.switchCharacterFour and Config.SWITCH_CHARACTER_STATE[self.hwnd][3],
            self.taskConfig.switchCharacterFive and Config.SWITCH_CHARACTER_STATE[self.hwnd][4],
            all(Config.SWITCH_CHARACTER_STATE[self.hwnd])
        ]

        if any(characterState):
            self.init()
            return '切换角色'

        return None
