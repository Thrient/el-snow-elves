from script.config.Config import Config
from script.task.basis.ClassisTask import ClassicTask


class SwitchCharacterTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self):
        if self.taskConfig.switchCharacterOne and Config.SWITCH_CHARACTER_STATE[self.hwnd][0]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][0] = False
            return
        if self.taskConfig.switchCharacterTwo and Config.SWITCH_CHARACTER_STATE[self.hwnd][1]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][1] = False
            return
        if self.taskConfig.switchCharacterThree and Config.SWITCH_CHARACTER_STATE[self.hwnd][2]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][2] = False
            return
        if self.taskConfig.switchCharacterFour and Config.SWITCH_CHARACTER_STATE[self.hwnd][3]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][3] = False
            return
        if self.taskConfig.switchCharacterFive and Config.SWITCH_CHARACTER_STATE[self.hwnd][4]:
            Config.SWITCH_CHARACTER_STATE[self.hwnd][4] = False
            return
        if all(Config.SWITCH_CHARACTER_STATE[self.hwnd]):
            Config.SWITCH_CHARACTER_STATE[self.hwnd][5] = False
            self.switchCharacterDefault()
            return
