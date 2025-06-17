from enum import Enum


class ManfalotyCommands(Enum):
    """
    ManfalotyCommands enumerates commands for controlling the manipulator.

    .. note::
       Each value is an integer that corresponds to a specific action.
    """

    GRIPPER_JAW_CLOSE = -1
    """Closes the gripper jaws."""

    GRIPPER_JAW_OPEN = 1
    """Opens the gripper jaws."""

    RELAY_ON = 2
    """Activates the pump."""

    RELAY_OFF = -2
    """Deactivates the pump."""

    PH_TAKE_READING = 4
    """Deactivates the LED."""

    RESET_MOTORS = 100
    """Resets all motors."""

    RESTART_ARDUINO = 1000
    """Restarts the Arduino controller."""
