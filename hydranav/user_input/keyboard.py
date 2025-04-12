import pygame
from user_input.keyboard_keys import KeyboardKeys
from user_input.input_mapper import input_mapper
from core import system_logger, event_dispatcher

__all__ = ["Keyboard", "KeyboardKeys"]


class Keyboard:
    def __init__(self):
        pass

    def update(self):
        for button_event in pygame.event.get([pygame.KEYDOWN]):
            processed_key = KeyboardKeys.from_pygame_key(button_event.key)
            if processed_key is None:
                system_logger.warning(
                    f"{button_event.key} is not a supported button"
                )
                continue
            input_mapper.button_down(f"K_{processed_key.name}")
            system_logger.info(
                f"keyboard button {KeyboardKeys.from_pygame_key(button_event.key).name} pressed down"
            )
