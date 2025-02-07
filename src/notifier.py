import pygame
from events import EventDispatcher
from pathlib import Path


class Notifier:
    def __init__(
        self, dispatcher: EventDispatcher, audio_assests_path: str = "./assets/audio"
    ):
        pygame.mixer.init()

        self.volume = 100

        self.__audio_assets_path = Path(audio_assests_path)
        self.__dispatcher = dispatcher

        self.__dispatcher.subscribe(
            "controller_connected", lambda _: self.play("controller_connected")
        )
        self.__dispatcher.subscribe(
            "controller_disconnected", lambda _: self.play("controller_disconnected")
        )

        self.__dispatcher.subscribe("gui_screen_cleared", lambda _: self.__change_volume(0))

    def __change_volume(self, inc: int):
        if self.volume + inc > 100:
            self.volume = 100
        elif self.volume + inc < 0:
            self.volume = 0
        else:
            self.volume += inc

        print(self.volume)

        pygame.mixer.music.set_volume(self.volume)
        self.__dispatcher.dispatch("notifier_volume_change", self.volume)

    def volume_up(self):
        self.__change_volume(10)

    def volume_down(self):
        self.__change_volume(-10)

    def play(self, file: str, blocking: bool = False):
        path = Path(self.__audio_assets_path, f"{file}.wav")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        while pygame.mixer.get_busy() and blocking:
            pygame.time.delay(100)
