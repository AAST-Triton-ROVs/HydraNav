from rov.enums import ControlChannels, Directions


class ROVMovement:
    def __init__(self, channel: ControlChannels, direction: Directions):
        self.channel = channel
        self.direction = direction

    def __eq__(self, value):
        if not isinstance(value, ROVMovement):
            return False

        return self.channel == value.channel and self.direction == value.direction
