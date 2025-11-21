from script.utils.Api import api


class SwitchCharacterScheduler:
    def __init__(self):
        self.switchCharacterOne = True
        self.switchCharacterTwo = True
        self.switchCharacterThree = True
        self.switchCharacterFour = True
        self.switchCharacterFive = True
        self.switchCharacterDefault = True

        api.on("SWITCH:CHARACTER:SCHEDULER:CLEAR", self.clear)

    def clear(self):
        self.switchCharacterOne = True
        self.switchCharacterTwo = True
        self.switchCharacterThree = True
        self.switchCharacterFour = True
        self.switchCharacterFive = True
        self.switchCharacterDefault = True

    @property
    def __list__(self):
        return [
            self.switchCharacterOne,
            self.switchCharacterTwo,
            self.switchCharacterThree,
            self.switchCharacterFour,
            self.switchCharacterFive,
            self.switchCharacterDefault
        ]


switchCharacterScheduler = SwitchCharacterScheduler()
