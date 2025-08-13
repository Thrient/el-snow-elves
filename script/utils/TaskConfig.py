class TaskConfig:
    def __init__(self, **kwargs):
        self.executeList = kwargs.get('executeList', [])
        self.model = kwargs.get('model', 'classic')
        self.switchCharacterOne = kwargs.get('switchCharacterOne', False)
        self.switchCharacterTwo = kwargs.get('switchCharacterTwo', False)
        self.switchCharacterThree = kwargs.get('switchCharacterThree', False)
        self.switchCharacterFour = kwargs.get('switchCharacterFour', False)
        self.switchCharacterFive = kwargs.get('switchCharacterFive', False)
