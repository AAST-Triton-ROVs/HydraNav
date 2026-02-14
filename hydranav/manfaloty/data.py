from abc import ABC

class ManfalotyData(ABC):
    """
    Base class for Manfaloty data.

    This class serves as a blueprint for all
    Manfaloty data objects.
    """


class PHReading(ManfalotyData):
    """
    Represents a pH reading.

    :param value: The pH value
    :type value: float
    """

    def __init__(self, value: float):
        self.value = value