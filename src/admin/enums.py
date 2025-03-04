from enum import Enum

class AdminCommands(Enum):
    POWEROFF = 0
    REBOOT = 1
    RESTART_MAVPROXY = 2
    RESTART_GRIPPER = 3
    RESTART_TELEMETRY = 4
    RESTART_ADMIN = 10