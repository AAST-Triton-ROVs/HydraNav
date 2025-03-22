from core import GCSModule, config_manager
from user_input.controller import Controller
from user_input.keyboard import Keyboard, KeyboardKeys  # noqa: F401

__all__ = ["UserInput", "KeyboardKeys"]


class UserInput(GCSModule):
    """
    UserInput class to handle user input through a controller.

    :param dispatcher: An instance of EventDispatcher to handle events.
    :type dispatcher: EventDispatcher
    :param joystick_deadzone_factor: The deadzone factor for the joystick, defaults to 2.
    :type joystick_deadzone_factor: float, optional
    :param joystick_roundoff: The roundoff value for the joystick, defaults to 1.
    :type joystick_roundoff: int, optional
    :param joystick_multiplier: The multiplier for the joystick, defaults to 100.
    :type joystick_multiplier: int, optional
    """

    def __init__(
        self
    ):
        """
        Initialize the UserInput class.

        :param dispatcher: An instance of EventDispatcher to handle events.
        :type dispatcher: EventDispatcher
        :param joystick_deadzone_factor: The deadzone factor for the joystick, defaults to 2.
        :type joystick_deadzone_factor: float, optional
        :param joystick_roundoff: The roundoff value for the joystick, defaults to 1.
        :type joystick_roundoff: int, optional
        :param joystick_multiplier: The multiplier for the joystick, defaults to 100.
        :type joystick_multiplier: int, optional
        """
        super().__init__()
        
        self.controller = Controller()
        self.keyboard = Keyboard()

    def quit(self):
        self.controller.quit()
        
    def status_ok(self) -> bool:
        return self.controller.status_ok()

    def update(self):
        self.controller.update()
        self.keyboard.update()
