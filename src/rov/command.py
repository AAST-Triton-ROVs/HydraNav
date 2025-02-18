from enum import Enum


class ROVCommands(Enum):
    DISARM = 0
    ARM = 1

    SYSTEM_MODE_MANUAL = 2
    SYSTEM_MODE_STABILIZE = 3

    GAIN_UP = 4
    GAIN_DOWN = 5
