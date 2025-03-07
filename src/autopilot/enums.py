from enum import Enum
from pymavlink import mavutil # type: ignore

class ControlChannels(Enum):
    """
    Control channels.

    :cvar PITCH: Pitch channel
    :cvar ROLL: Roll channel
    :cvar THROTTLE: Throttle channel
    :cvar YAW: Yaw channel
    :cvar FORWARD: Forward channel
    :cvar LATERAL: Lateral channel
    """
    PITCH = 1
    ROLL = 2
    THROTTLE = 3
    YAW = 4
    FORWARD = 5
    LATERAL = 6


class Directions(Enum):
    """
    Directions.

    :cvar NEGATIVE: Negative direction
    :cvar NEUTRAL: Neutral direction
    :cvar POSITIVE: Positive direction
    """
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1


class ToggleStates(Enum):
    """
    Toggle states.

    :cvar ON: The toggle is on
    :cvar OFF: The toggle is off
    """
    ON = 1
    OFF = 0


class SystemModes(Enum):
    """
    Possible system modes for vehicle control.

    :cvar STABILIZATION: Stability-oriented flight
    :cvar ACRO: Manual rate control
    :cvar ALT_HOLD: Altitude hold
    :cvar AUTO: Autonomous mode
    :cvar GUIDED: Guided mode with external instructions
    :cvar CIRCLE: Circular flight path
    :cvar SURFACE: Surface navigation mode
    :cvar POSHOLD: Position hold
    :cvar MANUAL: Full manual control
    """
    STABILIZATION = 0
    ACRO = 1
    ALT_HOLD = 2
    AUTO = 3
    GUIDED = 4
    CIRCLE = 7
    SURFACE = 9
    POSHOLD = 16
    MANUAL = 19

class ArdusubParameters(Enum):
    FRAME_CONFIG = mavutil.mavlink.FRAME_CONFIG
    FS_LEAK_ENABLE = mavutil.mavlink.FS_LEAK_ENABLE
    FS_PILOT_INPUT = mavutil.mavlink.FS_PILOT_INPUT
    FS_PILOT_TIMEOUT = mavutil.mavlink.FS_PILOT_TIMEOUT
    LEAK1_PIN = mavutil.mavlink.LEAK1_PIN
    LEAK1_LOGIC = mavutil.mavlink.LEAK1_LOGIC
    LOG_BACKEND_TYPE = mavutil.mavlink.LOG_BACKEND_TYPE
    