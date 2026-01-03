from script.core.TaskConfigScheduler import taskConfigScheduler
from script.task.basis.classic.ClassicTask import ClassicTask


class SwitchCharacterTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = taskConfigScheduler.config[self.hwnd]["配置"]

    def execute(self):
        if "characterOne" in self.config.switchCharacterList and taskConfigScheduler.config[self.hwnd]["角色"][0]:
            self.switchCharacterOne()
            taskConfigScheduler.config[self.hwnd]["角色"][0] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterOne")
        elif "characterTwo" in self.config.switchCharacterList and taskConfigScheduler.config[self.hwnd]["角色"][1]:
            self.switchCharacterTwo()
            taskConfigScheduler.config[self.hwnd]["角色"][1] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterTwo")
        elif "characterThree" in self.config.switchCharacterList and taskConfigScheduler.config[self.hwnd]["角色"][2]:
            self.switchCharacterThree()
            taskConfigScheduler.config[self.hwnd]["角色"][2] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterThree")
        elif "characterFour" in self.config.switchCharacterList and taskConfigScheduler.config[self.hwnd]["角色"][3]:
            self.switchCharacterFour()
            taskConfigScheduler.config[self.hwnd]["角色"][3] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterFour")
        elif "characterFive" in self.config.switchCharacterList and taskConfigScheduler.config[self.hwnd]["角色"][4]:
            self.switchCharacterFive()
            taskConfigScheduler.config[self.hwnd]["角色"][4] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterFive")
        elif all(taskConfigScheduler.config[self.hwnd]["角色"]):
            self.switchCharacterDefault()
            taskConfigScheduler.config[self.hwnd]["角色"][5] = False
            taskConfigScheduler.setCharacter(self.hwnd, "characterDefault")
