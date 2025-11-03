from script.core.SwitchCharacterScheduler import switchCharacterScheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.task.basis.ClassicTask import ClassicTask
from script.utils.Api import api


class SwitchCharacterTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def instance(self):
        return self

    def execute(self):
        if "characterOne" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterOne:
            switchCharacterScheduler.switchCharacterOne = False
            self.switchCharacterOne()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
        if "characterTwo" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterTwo:
            switchCharacterScheduler.switchCharacterTwo = False
            self.switchCharacterTwo()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
        if "characterThree" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterThree:
            switchCharacterScheduler.switchCharacterThree = False
            self.switchCharacterThree()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
        if "characterFour" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterFour:
            switchCharacterScheduler.switchCharacterFour = False
            self.switchCharacterFour()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
        if "characterFive" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterFive:
            switchCharacterScheduler.switchCharacterFive = False
            self.switchCharacterFive()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
        if all(switchCharacterScheduler.__list__):
            switchCharacterScheduler.switchCharacterDefault = False
            self.switchCharacterDefault()
            api.emit("TASK:CONFIG:SCHEDULER:SYNC")

            return
