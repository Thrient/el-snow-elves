from script.utils.Api import api
from script.utils.TaskConfig import TaskConfig


class TaskConfigScheduler:

    def __init__(self):
        self.common = TaskConfig()
        self.config = TaskConfig()
        api.on("TASK:CONFIG:SCHEDULER:SYNC", self.sync)

    def init(self, config, **kwargs):
        self.common = TaskConfig(**kwargs) if config == "默认配置" else TaskConfig().loadConfig(config)

    def load(self, config):
        self.config = TaskConfig().loadConfig(config)

    def sync(self):
        self.config = self.common


taskConfigScheduler = TaskConfigScheduler()
