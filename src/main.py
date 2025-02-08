import sys
import pygame
from controller import Controller
from events import EventDispatcher
from gui import GUI
from notifier import Notifier
from logger import Logging

class GCS:
    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()
        self.dispatcher = EventDispatcher()
        self.logging = Logging()

        self.gui = GUI("GCS", self.dispatcher, self.logging, self.clock)
        self.notifier = Notifier(self.dispatcher)
        self.controller = Controller(self.dispatcher, self.logging)
        
        self.gui.init_ui()
        self.controller.update_connection_status()

        self.dispatcher.subscribe("controller_button", self.on_controller_button)
        self.dispatcher.subscribe("gui_key", self.on_gui_key)
    def on_controller_button(self, key: int):
        match key:
            case 10:
                self.controller.calibrate()

    def on_gui_key(self, key: int):
        match key:
            case pygame.K_q:
                self.quit()
            case pygame.K_t:
                self.gui.toggle_theme()
            case pygame.K_UP:
                self.notifier.volume_up()
            case pygame.K_DOWN:
                self.notifier.volume_down()

    def run(self):
        while True:
            self.controller.update()
            self.gui.update()

            self.clock.tick(60)

    def quit(self):
        sys.exit()


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
