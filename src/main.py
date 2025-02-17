import sys
import pygame
from controller import Controller
from events import EventDispatcher
from gui import GUI
from notifier import Notifier
from logger import Logging
from pi_telemetry import PiTelemetery
from rov import ROV


class GCS:
    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()
        self.dispatcher = EventDispatcher()
        self.logging = Logging()

        # self.gui = GUI(self.dispatcher, self.logging)
        self.controller = Controller(self.dispatcher, self.logging)
        self.notifier = Notifier(self.dispatcher, self.logging)
        self.pi_telemetery = PiTelemetery(self.dispatcher, self.logging)
        self.rov = ROV(self.dispatcher, self.logging)

        self.controller.update_connection_status()

        self.dispatcher.subscribe("controller_button", self.on_controller_button)

    def on_controller_button(self, button: set):
        if button == "L":
            self.notifier.play("dua")
        elif button == "M":
            self.controller.calibrate()
        elif button == "A":
            self.rov.arm()
        elif button == "B":
            self.rov.disarm()
        elif button == "C":
            self.rov.flight_mode_stabilize()
        elif button == "D":
            self.rov.flight_mode_manual()
        elif button == "3":
            self.rov.gain_up()
        elif button == "1":
            self.rov.gain_down()
        elif button == "2" or button == "R4":
            # TODO: MAP TO GRIPPER FUNCTION
            pass
        elif button == "4" or button == "L4":
            # TODO: MAP TO GRIPPER FUNCTION
            pass

    def run(self):
        while True:
            # time_delta = (
            #     self.clock.tick(60) / 1000.0
            # )  # .tick return the time sinze last frame in milliseconds so we must divide it by 1000.0

            self.controller.update()
            # self.gui.update(time_delta)
            self.pi_telemetery.update()
            self.rov.update()

            self.clock.tick(60)

    def quit(self):
        self.pi_telemetery.close()
        sys.exit()


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
