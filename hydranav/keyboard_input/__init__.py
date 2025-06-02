from hydranav.keyboard_input.keyboard_keys import KeyboardKeys
from hydranav.core import input_mapper, GCSModule
from pynput import keyboard


class KeyboardInput(GCSModule):
    def __init__(self):
        self.__listener = keyboard.Listener(on_press=self.__on_key_press)
        self.__listener.start()
    
    @classmethod
    def init_order(cls):
        return 100

    def __on_key_press(self, key):
        keyboard_key = KeyboardKeys.from_pynput(key)
        if keyboard_key is None:
            return

        input_mapper.digital_input(f"K_{keyboard_key.name}")

    def status_ok(self):
        return self.__listener.is_alive()

    def quit(self):
        self.__listener.stop()
        self.__listener.join()
