from enum import Enum

class AdminCommands(Enum):
    """
    Enum of administrative commands.

    .. note::
       Keep these commands consistent with the system's admin interface.
    """

    POWEROFF = 0
    """Power off the system."""

    REBOOT = 1
    """Reboot the system."""

    RESTART_MAVPROXY = 2
    """Restart the MAVProxy process."""

    RESTART_GRIPPER = 3
    """Restart the gripper control process."""

    RESTART_TELEMETRY = 4
    """Restart the telemetry system."""

    RESTART_ADMIN = 10
    """Restart the admin interface."""