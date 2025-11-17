from script.core.SwitchCharacterScheduler import switchCharacterScheduler
from script.core.TaskConfigScheduler import taskConfigScheduler
from script.task.basis.ClassicTask import ClassicTask


class SwitchCharacterTask(ClassicTask):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def instance(self):
        return self

    def execute(self):
        if "characterOne" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterOne:
            switchCharacterScheduler.switchCharacterOne = False
            self.switchCharacterOne()


            return
        if "characterTwo" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterTwo:
            switchCharacterScheduler.switchCharacterTwo = False
            self.switchCharacterTwo()


            return
        if "characterThree" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterThree:
            switchCharacterScheduler.switchCharacterThree = False
            self.switchCharacterThree()

            return
        if "characterFour" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterFour:
            switchCharacterScheduler.switchCharacterFour = False
            self.switchCharacterFour()


            return
        if "characterFive" in taskConfigScheduler.common.switchCharacterList and switchCharacterScheduler.switchCharacterFive:
            switchCharacterScheduler.switchCharacterFive = False
            self.switchCharacterFive()

            return
        if all(switchCharacterScheduler.__list__):
            switchCharacterScheduler.switchCharacterDefault = False
            self.switchCharacterDefault()


            return
