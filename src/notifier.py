import pygame
from events import EventDispatcher
from pathlib import Path
from logger import logging

__exports__ = ["Notifier"]


class Notifier:
    """
    A class to handle audio notifications for various events.
    
    :param dispatcher: An instance of EventDispatcher to subscribe to events.
    :type dispatcher: EventDispatcher
   
    :param audio_assests_path: Path to the directory containing audio assets, defaults to "./assets/audio".
    :type audio_assests_path: str
    
    Methods
    -------
    volume_up():
        Increases the volume by 10 units.
    volume_down():
        Decreases the volume by 10 units.
    play(file: str):
        Plays the specified audio file.
    
    Private Methods
    ---------------
    __change_volume(inc: int):
        Changes the volume by the specified increment.
    """
    
    def __init__(
        self,
        dispatcher: EventDispatcher,
        audio_assests_path: str = "./assets/audio",
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
        """
        Adjust the volume by a specified increment.

        This method changes the volume by the given increment, ensuring that the
        volume remains within the range of 0 to 100. It then updates the volume
        in the pygame mixer and dispatches a notification about the volume change.

        :param inc: The increment by which to adjust the volume. Positive values
                    increase the volume, while negative values decrease it.
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
        Increase the notifier volume by a fixed amount.
        This method increases the volume of the notifier by 10 units and logs the new volume level.
        
        :return: None
        """
        
        self.__change_volume(10)
        logging.logger.info(f"Notifier volume up: {self.volume}")

    def volume_down(self):
        """
        Decrease the notifier volume by a fixed amount.
        This method decreases the volume by 10 units and logs the new volume level.
        
        :return: None
        """
        
        self.__change_volume(-10)
        logging.logger.info(f"Notifier volume down: {self.volume}")

    def play(self, file: str):
        """
        Play an audio file.
        This method constructs the path to the audio file using the provided
        filename and the internal audio assets path, then loads and plays
        the audio file using the pygame mixer.
        
        :param file: The name of the audio file to play (without extension).
        :type file: str
        """
        
        path = Path(self.__audio_assets_path, f"{file}.wav")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
