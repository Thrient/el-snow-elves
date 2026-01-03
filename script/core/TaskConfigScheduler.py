from script.utils.TaskConfig import TaskConfig


class TaskConfigScheduler:

    def __init__(self):
        self.config = {}

    def init(self, hwnd, config, kwargs):
        cls = TaskConfig(**kwargs) if config == "当前配置" else TaskConfig().loadConfig(config)
        self.config[hwnd] = {
            "配置": cls,
            "当前角色": "characterDefault",
            "角色": [True, True, True, True, True, True],
        }

    def setCharacter(self, hwnd, character):
        self.config[hwnd]["当前角色"] = character

    def loadConfig(self, hwnd):
        return self.config[hwnd]["配置"]


taskConfigScheduler = TaskConfigScheduler()
