from enum import Enum


class ControlChannels(Enum):
    PITCH = 1
    ROLL = 2
    THROTTLE = 3
    YAW = 4
    FORWARD = 5
    LATERAL = 6


class Directions(Enum):
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1


class ToggleStates(Enum):
    ON = 1
    OFF = 0


class SystemModes(Enum):
    """
    Output from Pixhwak
    ```
    {
        'STABILIZE': 0,
        'ACRO': 1,
        'ALT_HOLD': 2,
        'AUTO': 3,
        'GUIDED': 4,
        'CIRCLE': 7,
        'SURFACE': 9
        'POSHOLD': 16,
        'MANUAL': 19,
    }
    ```
    """

    STABILIZE = 0
    ACRO = 1
    ALT_HOLD = 2
    AUTO = 3
    GUIDED = 4
    CIRCLE = 7
    SURFACE = 9
    POSHOLD = 16
    MANUAL = 19
