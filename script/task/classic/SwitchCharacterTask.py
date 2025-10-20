from script.config.Config import Config
from script.core.TaskConfigScheduler import task_config_scheduler
from script.task.basis.ClassicTask import ClassicTask


class SwitchCharacterTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def instance(self):
        return self

    def execute(self):
        if "characterOne" in self.taskConfig.switchCharacterList and Config.SWITCH_CHARACTER_STATE[self.hwnd][0]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][0] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterOne()
            return
        if "characterTwo" in self.taskConfig.switchCharacterList and Config.SWITCH_CHARACTER_STATE[self.hwnd][1]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][1] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterTwo()
            return
        if "characterThree" in self.taskConfig.switchCharacterList and Config.SWITCH_CHARACTER_STATE[self.hwnd][2]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][2] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterThree()
            return
        if "characterFour" in self.taskConfig.switchCharacterList and Config.SWITCH_CHARACTER_STATE[self.hwnd][3]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][3] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterFour()
            return
        if "characterFive" in self.taskConfig.switchCharacterList and Config.SWITCH_CHARACTER_STATE[self.hwnd][4]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][4] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterFive()
            return
        if all(Config.SWITCH_CHARACTER_STATE[self.hwnd]):
            Config.SWITCH_CHARACTER_STATE[self.hwnd][5] = False
            config = task_config_scheduler.read_common(self.hwnd)
            task_config_scheduler.load(hwnd=self.hwnd, arg=config)
            self.switchCharacterDefault()
            return
