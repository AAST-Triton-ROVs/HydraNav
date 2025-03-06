import pygame
from events import EventDispatcher
from user_input.keyboard_keys import KeyboardKeys
from logger import system_logger

__all__ = ["Keyboard", "KeyboardKeys"]


class Keyboard:
    def __init__(self, dispatcher: EventDispatcher):
        self.__dispatcher = dispatcher

    def update(self):
        for button_event in pygame.event.get([pygame.KEYDOWN]):
            self.__dispatcher.dispatch(
                "keyboard_button_down",
                KeyboardKeys.from_pygame_key(button_event.key),
            )
            system_logger.info(
                f"keyboard button {KeyboardKeys.from_pygame_key(button_event.key).value} pressed down"
            )

        for button_event in pygame.event.get([pygame.KEYUP]):
            self.__dispatcher.dispatch(
                "keyboard_button_up",
                KeyboardKeys.from_pygame_key(button_event.key),
            )
            system_logger.info(
                f"keyboard button {KeyboardKeys.from_pygame_key(button_event.key).value} pressed up"
            )
