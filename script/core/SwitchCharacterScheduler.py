class SwitchCharacterScheduler:
    def __init__(self):
        self.switchCharacterOne = True
        self.switchCharacterTwo = True
        self.switchCharacterThree = True
        self.switchCharacterFour = True
        self.switchCharacterFive = True
        self.switchCharacterDefault = True

    def reset(self):
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
