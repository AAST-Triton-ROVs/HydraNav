from abc import ABC, abstractmethod


class ManfalotyData(ABC):
    @abstractmethod
    @property
    def value(self):
        pass

class PHReading(ManfalotyData):
    def __init__(self, value: float):
        self.__value = value

    @property
    def value(self):
        return self.__value