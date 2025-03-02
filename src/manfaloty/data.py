from abc import ABC


class ManfalotyData(ABC):
    pass

class PHReading(ManfalotyData):
    def __init__(self, value: float):
        self.value = value