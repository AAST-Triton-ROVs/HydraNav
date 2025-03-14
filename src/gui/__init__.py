from typing import Optional, Tuple
import pygame
from core.event_dispatcher import EventDispatcher
from core.gcs_module import GCSModule
from core.logger import system_logger
from pygame_gui import UIManager

from core.request_manager import RequestManager

# armed or disarmed
# max gain
# current thottle
# current pitch
# current roll
# current yaw
# pi cpu usage
# pi memory usage
# pi temperature
# joystick


class GUI(GCSModule):
    def __init__(
        self,
        dispatcher: EventDispatcher,
        request_manager: RequestManager,
    ):
        super().__init__(dispatcher, request_manager)

        pygame.display.set_caption("Triton GCS")
        self.window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.ui_manager = UIManager(
            self.__get_resolution(),
            # PackageResource(package="assets", resource="theme_2.json"),
        )

    def quit(self):
        return

    def update(self, time_delta: float | int):
        self.ui_manager.update(time_delta)

        self.ui_manager.draw_ui(self.window_surface)

        pygame.display.update()

    def __get_resolution(self) -> Tuple[int, int]:
        return pygame.display.get_window_size()
