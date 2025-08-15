from script.task.classic.LessonTask import LessonTask
from script.task.classic.SwitchCharacterTask import SwitchCharacterTask


class TaskFactory:
    __instance = None

    def __init__(self):
        self.tasks = {}
        self.init()

    @staticmethod
    def instance():
        """
        获取TaskFactory的单例实例

        Returns:
            TaskFactory: 返回TaskFactory的单例实例
        """
        if TaskFactory.__instance is None:
            TaskFactory.__instance = TaskFactory()
        return TaskFactory.__instance

    def init(self):
        """
        初始化函数，用于注册课业任务类型

        参数:
            self: 类实例对象

        返回值:
            无
        """
        # 注册经典课业任务类型
        self.register("classic", "课业任务", LessonTask)
        self.register("classic", "切换角色", SwitchCharacterTask)

    def register(self, model, name, task):
        """
        注册任务类型

        Args:
            model (str): 任务模型类型
            name (str): 任务名称
            task (class): 任务类
        """
        if model not in self.tasks:
            self.tasks[model] = {}
        self.tasks[model][name] = task

    def create(self, model, name):
        """
        创建任务实例

        Args:
            model (str): 任务模型类型
            name (str): 任务名称

        Returns:
            class: 返回对应的任务类，如果未找到则返回None
        """
        # 检查模型是否存在
        if model not in self.tasks:
            return None

        return self.tasks[model][name]
