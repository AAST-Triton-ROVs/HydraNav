class ROVMovement:
    """
    Represents the movement state of an ROV.

    :param forward: Forward movement value.
    :type forward: float
    :param lateral: Lateral movement value.
    :type lateral: float
    :param throttle: Vertical throttle control.
    :type throttle: float
    :param yaw: Yaw rotation value.
    :type yaw: float
    :param roll: Roll rotation value.
    :type roll: float
    """

    def __init__(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        self.forward = forward
        self.lateral = lateral
        self.throttle = throttle
        self.yaw = yaw
        self.roll = roll

    def __eq__(self, value):
        """
        Checks equality with another ROVMovement instance.

        :param value: Another ROVMovement object.
        :type value: ROVMovement
        :return: True if equal, False otherwise.
        :rtype: bool
        """
        if not isinstance(value, ROVMovement):
            return False

        return (
            self.forward == value.forward
            and self.lateral == value.lateral
            and self.throttle == value.throttle
            and self.yaw == value.yaw
            and self.roll == value.roll
        )
