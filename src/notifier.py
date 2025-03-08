import pygame
from events import EventDispatcher
from pathlib import Path
from logger import system_logger
from requests import RequestManager

__all__ = ["Notifier"]


class Notifier:
    """
    Handles audio notifications for various events.

    :param dispatcher: An instance of EventDispatcher used to subscribe to events.
    :type dispatcher: EventDispatcher
    :param audio_assests_path: Path to the directory containing audio assets.
                               Defaults to "./assets/audio".
    :type audio_assests_path: str

    .. note::

       This class provides methods to increase or decrease the volume and to play audio files.
       It automatically subscribes to several events and triggers corresponding audio notifications.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        request_manager: RequestManager,
        audio_assests_path: str = "./assets/audio",
    ):
        pygame.mixer.init()

        self.volume = 100

        self.__audio_assets_path = Path(audio_assests_path)
        self.__dispatcher = dispatcher
        self.__request_manager = request_manager

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
        self.__request_manager.register_handler("notifier_get_volume", self.__dispatch_volume)

        self.__change_volume(self.volume)
        
    def __dispatch_volume(self):
        self.__dispatcher.dispatch("notifier_volume_state", self.volume)

    def __change_volume(self, inc: int):
        """
        Adjust the volume by a specified increment.

        The new volume is clamped between 0 and 100. After updating the volume,
        it sets the new volume on the pygame mixer and dispatches a notification event
        with the updated volume.

        :param inc: The amount to change the volume by. Positive values increase the volume whilst
                    negative values decrease it.
        :type inc: int
        """
        if self.volume + inc > 100:
            self.volume = 100
        elif self.volume + inc < 0:
            self.volume = 0
        else:
            self.volume += inc

        pygame.mixer.music.set_volume(self.volume)
        self.__dispatcher.dispatch("notifier_volume_change", self.volume)

    def volume_up(self):
        """
        Increase the notifier volume by 10 units.

        This method calls a private function to adjust the volume and then logs the new volume level.

        :return: None
        """
        self.__change_volume(10)
        system_logger.info(f"Notifier volume up: {self.volume}")

    def volume_down(self):
        """
        Decrease the notifier volume by 10 units.

        This method calls a private function to adjust the volume and then logs the new volume level.

        :return: None
        """
        self.__change_volume(-10)
        system_logger.info(f"Notifier volume down: {self.volume}")

    def play(self, file: str):
        """
        Play an audio file.

        Constructs the full path to the audio file (assumed to be in WAV format)
        using the provided file name and the internal audio assets path, then loads
        and plays the audio file using the pygame mixer.

        :param file: The name of the audio file to play, without the extension.
        :type file: str
        :return: None
        """
        path = Path(self.__audio_assets_path, f"{file}.wav")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
