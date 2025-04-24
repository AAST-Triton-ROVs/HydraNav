from user_input.keyboard_keys import KeyboardKeys
from user_input.input_mapper import input_mapper
from pynput import keyboard

__all__ = ["Keyboard", "KeyboardKeys"]


class Keyboard:
    def __init__(self):
        self.__listener = keyboard.Listener(on_press=self.__on_key_press)
        self.__listener.start()

    def __on_key_press(self, key):
        keyboard_key = KeyboardKeys.from_pynput(key)
        if keyboard_key is None:
            return

        input_mapper.button_down(f"K_{keyboard_key.name}")

    def quit(self):
        self.__listener.stop()
        self.__listener.join()
