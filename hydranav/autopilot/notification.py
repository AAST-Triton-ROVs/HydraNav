from autopilot.enums import SystemModes


class ROVNotification:
    """
    .. class:: ROVNotification

       Base class for ROV notifications.

    :param priority: Notification priority.
    :type priority: int
    """

    def __init__(self, priority: int):
        """
        :param priority: Notification priority.
        :type priority: int
        """
        self.priority = priority

    def __lt__(self, other):
        """
        Compare priorities with another ROVNotification.

        :param other: Another ROVNotification instance.
        :type other: ROVNotification
        :return: True if this notification has a lower priority.
        :rtype: bool
        """
        if not isinstance(other, ROVNotification):
            return False
        return self.priority < other.priority


class VehicleDisconnected(ROVNotification):
    """
    .. class:: VehicleDisconnected

       Notification for vehicle disconnection.
    """
    def __init__(self):
        """
        Initialize with a fixed priority for vehicle disconnection.
        """
        super().__init__(1)


class VehicleConnected(ROVNotification):
    """
    .. class:: VehicleConnected

       Notification for vehicle connection.
    """
    def __init__(self):
        """
        Initialize with a fixed priority for vehicle connection.
        """
        super().__init__(2)


class Armed(ROVNotification):
    """
    .. class:: Armed

       Notification for an armed vehicle state.
    """
    def __init__(self):
        """
        Initialize with a fixed priority for an armed state.
        """
        super().__init__(3)


class Disarmed(ROVNotification):
    """
    .. class:: Disarmed

       Notification for a disarmed vehicle state.
    """
    def __init__(self):
        """
        Initialize with a fixed priority for a disarmed state.
        """
        super().__init__(4)


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
        super().__init__(10)
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
        super().__init__(11)
        self.mode = mode
