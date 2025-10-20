from typing import overload

from script.utils.TaskConfig import TaskConfig


class TaskConfigScheduler:
    def __init__(self):
        self._dict = {}
        self._common_dict = {}



    def load(self, hwnd, arg: str | TaskConfig) -> None:
        if isinstance(arg, str):
            self._dict[hwnd] = TaskConfig().loadConfig(arg)
        else:
            self._dict[hwnd] = arg

    def load_common(self, hwnd, config):
        self._common_dict[hwnd] = config

    def read(self, hwnd):
        if hwnd not in self._dict:
            return TaskConfig()
        return self._dict[hwnd]

    def read_common(self, hwnd):
        if hwnd not in self._common_dict:
            return TaskConfig()
        return self._common_dict[hwnd]


task_config_scheduler = TaskConfigScheduler()
