import queue

from script.core.SwitchCharacterScheduler import switchCharacterScheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.utils.Api import api


class TaskScheduler:

    def __init__(self):
        self.counter = 0
        self.queue = queue.PriorityQueue()
        self.tasks = set()
        api.on("TASK:SCHEDULER:INIT", self.init)

    def init(self):
        self.queue = queue.PriorityQueue()
        self.tasks.clear()
        self.counter = 0
        for task in taskConfigScheduler.config.executeList:
            self.add(0, task["data"])

    def clear(self):
        self.queue = queue.PriorityQueue()
        self.tasks.clear()

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
            "characterOne" in taskConfigScheduler.common.switchCharacterList and
            switchCharacterScheduler.switchCharacterOne,
            "characterTwo" in taskConfigScheduler.common.switchCharacterList and
            switchCharacterScheduler.switchCharacterTwo,
            "characterThree" in taskConfigScheduler.common.switchCharacterList and
            switchCharacterScheduler.switchCharacterThree,
            "characterFour" in taskConfigScheduler.common.switchCharacterList and
            switchCharacterScheduler.switchCharacterFour,
            "characterFive" in taskConfigScheduler.common.switchCharacterList and
            switchCharacterScheduler.switchCharacterFive,
            all(switchCharacterScheduler.__list__)
        ]

        if any(characterState):
            api.emit("TASK:SCHEDULER:INIT")
            return '切换角色'
        return None


taskScheduler = TaskScheduler()
