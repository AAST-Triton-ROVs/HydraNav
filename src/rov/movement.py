

class ROVMovement:
    def __init__(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        self.forward = forward
        self.lateral = lateral
        self.throttle = throttle
        self.yaw = yaw
        self.roll = roll

    def __eq__(self, value):
        if not isinstance(value, ROVMovement):
            return False

        return (
            self.forward == value.forward
            and self.lateral == value.lateral
            and self.throttle == value.throttle
            and self.yaw == value.yaw
            and self.roll == value.roll
        )
