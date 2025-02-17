import pygame
from events import EventDispatcher
from pathlib import Path
from logger import Logging

__exports__ = ["Notifier"]

class Notifier:
    def __init__(
        self,
        dispatcher: EventDispatcher,
        logging: Logging,
        audio_assests_path: str = "./assets/audio",
    ):
        pygame.mixer.init()

        self.volume = 100

        self.__audio_assets_path = Path(audio_assests_path)
        self.__dispatcher = dispatcher
        self.__logging = logging

        self.__dispatcher.subscribe(
            "controller_connected", lambda _: self.play("controller_connected")
        )
        self.__dispatcher.subscribe(
            "controller_disconnected", lambda _: self.play("controller_disconnected")
        )

        self.__dispatcher.subscribe("rov_armed", lambda _: self.play("armed"))
        self.__dispatcher.subscribe("rov_disarmed", lambda _: self.play("disarmed"))
        self.__dispatcher.subscribe(
            "rov_gain_change", lambda g: self.play(f"{g}_percent_gain")
        )
        self.__dispatcher.subscribe(
            "rov_vehicle_connected", lambda _: self.play("vehicle_connected")
        )
        self.__dispatcher.subscribe(
            "rov_vehicle_disconnected", lambda _: self.play("vehicle_disconnected")
        )
        self.__dispatcher.subscribe(
            "rov_system_mode_changed", lambda m: self.play(f"{m.name.lower()}_mode")
        )

        self.__change_volume(self.volume)

    def __change_volume(self, inc: int):
        if self.volume + inc > 100:
            self.volume = 100
        elif self.volume + inc < 0:
            self.volume = 0
        else:
            self.volume += inc

        pygame.mixer.music.set_volume(self.volume)
        self.__dispatcher.dispatch("notifier_volume_change", self.volume)

    def volume_up(self):
        self.__change_volume(10)
        self.__logging.logger.info(f"Notifier volume up: {self.volume}")

    def volume_down(self):
        self.__change_volume(-10)
        self.__logging.logger.info(f"Notifier volume down: {self.volume}")

    def play(self, file: str):
        path = Path(self.__audio_assets_path, f"{file}.wav")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

