from enum import Enum

class ROVCommands(Enum):
    """
    :class:`ROVCommands`
    
    Provides commands for controlling the Remotely Operated Vehicle (ROV).
    """

    DISARM = 0
    """
    :const:`DISARM`
    
    Disarms the ROV.
    """

    ARM = 1
    """
    :const:`ARM`
    
    Arms the ROV.
    """

    SYSTEM_MODE_MANUAL = 2
    """
    :const:`SYSTEM_MODE_MANUAL`
    
    Sets the ROV to manual control mode.
    """

    SYSTEM_MODE_STABILIZE = 3
    """
    :const:`SYSTEM_MODE_STABILIZE`
    
    Sets the ROV to stabilize control mode.
    """

    GAIN_UP = 4
    """
    :const:`GAIN_UP`
    
    Increases the control gain.
    """

    GAIN_DOWN = 5
    """
    :const:`GAIN_DOWN`
    
    Decreases the control gain.
    """
