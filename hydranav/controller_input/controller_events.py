from abc import ABC


class ControllerEvents(ABC): ...


class ButtonDown(ControllerEvents):
    def __init__(self, button: str):
        super().__init__()
        self.button = button


class ButtonHold(ControllerEvents):
    def __init__(self, button: str):
        super().__init__()
        self.button = button


class AbsoluteAxisMotion(ControllerEvents):
    def __init__(self, axis: str, value: int):
        super().__init__()
        self.axis = axis
        self.value = value


class ControllerConnected(ControllerEvents):
    def __init__(self, name: str):
        super().__init__()
        self.device_name = name


class ControllerDisconnected(ControllerEvents): ...
