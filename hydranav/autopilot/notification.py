from autopilot.enums import SystemModes


class ROVNotification:
    """
    .. class:: ROVNotification

       Base class for ROV notifications.
    """

    pass


class VehicleDisconnected(ROVNotification):
    """
    .. class:: VehicleDisconnected

        Notification for vehicle disconnection.
    """

    def __init__(self):
        """
        Initialize with a fixed priority for vehicle disconnection.
        """
        super().__init__()


class VehicleConnected(ROVNotification):
    """
    .. class:: VehicleConnected

       Notification for vehicle connection.
    """

    def __init__(self):
        """
        Initialize with a fixed priority for vehicle connection.
        """
        super().__init__()


class Armed(ROVNotification):
    """
    .. class:: Armed

       Notification for an armed vehicle state.
    """

    def __init__(self):
        """
        Initialize with a fixed priority for an armed state.
        """
        super().__init__()


class Disarmed(ROVNotification):
    """
    .. class:: Disarmed

       Notification for a disarmed vehicle state.
    """

    def __init__(self):
        """
        Initialize with a fixed priority for a disarmed state.
        """
        super().__init__()


class GainChange(ROVNotification):
    """
    .. class:: GainChange

       Notification for adjusting gain.

    :param new_gain: New gain value.
    :type new_gain: int
    """

    def __init__(self, new_gain: int):
        """
        :param new_gain: New gain value.
        :type new_gain: int
        """
        super().__init__()
        self.new_gain = new_gain


class SystemModeChanged(ROVNotification):
    """
    .. class:: SystemModeChanged

       Notification for a system mode change.

    :param mode: New system mode.
    :type mode: SystemModes
    """

    def __init__(self, mode: SystemModes):
        """
        :param mode: New system mode.
        :type mode: SystemModes
        """
        super().__init__()
        self.mode = mode
