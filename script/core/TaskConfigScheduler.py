from script.utils.Api import api
from script.utils.TaskConfig import TaskConfig


class TaskConfigScheduler:

    def __init__(self):
        self.common = TaskConfig()
        self.config = TaskConfig()
        api.on("TASK:CONFIG:SCHEDULER:INIT", self.init)
        api.on("TASK:CONFIG:SCHEDULER:LOAD", self.load)

    def init(self, config, kwargs):
        self.common = TaskConfig(**kwargs) if config == "当前配置" else TaskConfig().loadConfig(config)
        self.config = self.common

    def load(self, config):
        self.config = self.common if config == "当前配置" else TaskConfig().loadConfig(config)


taskConfigScheduler = TaskConfigScheduler()
