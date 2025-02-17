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
        match button:
            case "L":
                self.notifier.play("dua")
            case "M":
                self.controller.calibrate()
            case "A":
                self.rov.arm()
            case "B":
                self.rov.disarm()
            case "C":
                self.rov.flight_mode_stabilize()
            case "D":
                self.rov.flight_mode_manual()
            case "3":
                self.rov.gain_up()
            case "1":
                self.rov.gain_down()
            case "R1":
                self.rov.gripper.open()
            case "L1":
                self.rov.gripper.close()
            case "R2":
                self.rov.gripper.roll_right()
            case "L2":
                self.rov.gripper.roll_left()
            case "2" | "R4":
                self.rov.gripper.pitch_up()
            case "4" | "L4":
                self.rov.gripper.pitch_down()

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
