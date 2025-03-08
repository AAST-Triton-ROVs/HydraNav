from event_dispatcher import EventDispatcher
from user_input.controller import Controller
from user_input.keyboard import Keyboard, KeyboardKeys  # noqa: F401

__all__ = ["UserInput", "KeyboardKeys"]

class UserInput:
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
        self,
        dispatcher: EventDispatcher,
        joystick_deadzone_factor: float = 2,
        joystick_roundoff: int = 1,
        joystick_multiplier: int = 100,
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
        self.__dispatcher = dispatcher
        self.controller = Controller(
            self.__dispatcher,
            joystick_deadzone_factor,
            joystick_roundoff,
            joystick_multiplier,
        )
        self.keyboard = Keyboard(self.__dispatcher)
        
    def update(self):
        self.controller.update()
        self.keyboard.update()
