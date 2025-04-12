import pygame
from pathlib import Path
from core import (
    event_dispatcher,
    request_manager,
    GCSModule,
    config_manager,
    system_logger,
)

__all__ = ["Notifier"]

AUDIO_ASSETS_PATH: str = config_manager.get("notifier", "assetsPath")


class Notifier(GCSModule):
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

    def __init__(self):
        super().__init__()

        pygame.mixer.init()

        self.volume = 100

        self.__audio_assets_path = Path(AUDIO_ASSETS_PATH)

        event_dispatcher.subscribe(
            "controller/connected", lambda _: self.play("controller_connected")
        )
        event_dispatcher.subscribe(
            "controller/disconnected", lambda _: self.play("controller_disconnected")
        )

        event_dispatcher.subscribe("rov/armed", lambda _: self.play("armed"))
        event_dispatcher.subscribe("rov/disarmed", lambda _: self.play("disarmed"))
        event_dispatcher.subscribe(
            "rov/gain_change", lambda g: self.play(f"{g}_percent_gain")
        )
        event_dispatcher.subscribe(
            "rov/vehicle_connected", lambda _: self.play("vehicle_connected")
        )
        event_dispatcher.subscribe(
            "rov/vehicle_disconnected", lambda _: self.play("vehicle_disconnected")
        )
        event_dispatcher.subscribe(
            "rov/system_mode_changed", lambda m: self.play(f"{m.name.lower()}_mode")
        )
        request_manager.register_handler("notifier/volume-get", self.__dispatch_volume)
        request_manager.register_handler("notifier/volume-up", self.__dispatch_volume)
        request_manager.register_handler("notifier/volume-down", self.__dispatch_volume)

    def __dispatch_volume(self):
        event_dispatcher.dispatch("notifier/volume_state", self.volume)

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
        event_dispatcher.dispatch("notifier/volume_change", self.volume)

    def quit(self):
        return

    def status_ok(self) -> bool:
        return True

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
