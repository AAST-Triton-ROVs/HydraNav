import pygame
from user_input.keyboard_keys import KeyboardKeys
from core import system_logger, event_dispatcher

__all__ = ["Keyboard", "KeyboardKeys"]


class Keyboard:
    def __init__(self):
        pass

    def update(self):
        for button_event in pygame.event.get([pygame.KEYDOWN]):
            event_dispatcher.dispatch(
                "keyboard_button_down",
                KeyboardKeys.from_pygame_key(button_event.key),
            )
            system_logger.info(
                f"keyboard button {KeyboardKeys.from_pygame_key(button_event.key).value} pressed down"
            )

        for button_event in pygame.event.get([pygame.KEYUP]):
            event_dispatcher.dispatch(
                "keyboard_button_up",
                KeyboardKeys.from_pygame_key(button_event.key),
            )
            system_logger.info(
                f"keyboard button {KeyboardKeys.from_pygame_key(button_event.key).value} pressed up"
            )
