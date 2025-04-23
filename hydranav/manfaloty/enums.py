from enum import Enum

class ManfalotyCommands(Enum):
    """
    ManfalotyCommands enumerates commands for controlling the manipulator.

    .. note::
       Each value is an integer that corresponds to a specific action.
    """

    GRIPPER_TOGGLE_JAW_CLOSE = 1
    """Closes the gripper jaws."""

    GRIPPER_TOGGLE_JAW_OPEN = -1
    """Opens the gripper jaws."""

    GRIPPER_PITCH_UP = 2
    """Moves the gripper pitch up."""

    GRIPPER_PITCH_DOWN = -2
    """Moves the gripper pitch down."""

    GRIPPER_ROLL_RIGHT = 3
    """Rolls the gripper to the right."""

    GRIPPER_ROLL_LEFT = -3
    """Rolls the gripper to the left."""

    CAMERA_PITCH_UP = 4
    """Moves the camera pitch up."""

    CAMERA_PITCH_DOWN = -4
    """Moves the camera pitch down."""

    PUMP_ON = 5
    """Activates the pump."""

    PUMP_OFF = -5
    """Deactivates the pump."""

    RESET_MOTORS = 100
    """Resets all motors."""

    RESTART_ARDUINO = 1000
    """Restarts the Arduino controller."""
