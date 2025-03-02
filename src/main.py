import sys
from typing import Tuple
import pygame
from controller import Controller
from events import EventDispatcher
from gui import GUI
from manfaloty import Manfaloty
from notifier import Notifier
from logger import logging
from pi_telemetry import PiTelemetery
from autopilot import Autopilot


class GCS:
    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()
        self.dispatcher = EventDispatcher()

        # self.gui = GUI(self.dispatcher, self.logging)
        self.controller = Controller(self.dispatcher)
        self.notifier = Notifier(self.dispatcher)
        self.pi_telemetery = PiTelemetery(self.dispatcher)
        
        self.autopilot = Autopilot(self.dispatcher)
        self.manfaloty = Manfaloty(self.dispatcher)

        self.controller.update_connection_status()

        self.dispatcher.subscribe(
            "controller_button",
            self.on_controller_button,
        )
        # self.dispatcher.subscribe(
        #     "controller_joysticks",
        #     self.handle_controller_joysticks,
        # )

    def handle_controller_joysticks(self, move: Tuple[float, float, float, float]):
        x, y, z, w = move

        self.autopilot.move(x, y, z, w, 0)

    def on_controller_button(self, button: str):
        print(button)
        match button:
            case "L":
                self.notifier.play("bolbol")
            case "M":
                self.controller.calibrate()
            case "A":
                self.autopilot.arm()
            case "B":
                self.autopilot.disarm()
            case "C":
                self.autopilot.flight_mode_stabilize()
            case "D":
                self.autopilot.flight_mode_manual()
            case "3":
                self.autopilot.gain_up()
            case "1":
                self.autopilot.gain_down()
            case "R1":
                self.manfaloty.gripper.open_jaws()
            case "L1":
                self.manfaloty.gripper.close_jaws()
            case "R2":
                self.manfaloty.gripper.roll_right()
            case "L2":
                self.manfaloty.gripper.roll_left()
            case "R4":
                self.manfaloty.gripper.pitch_up()
            case "L4":
                self.manfaloty.gripper.pitch_down()

    def run(self):
        while True:
            # time_delta = (
            #     self.clock.tick(60) / 1000.0
            # )  # .tick return the time sinze last frame in milliseconds so we must divide it by 1000.0

            self.controller.update()
            # self.gui.update(time_delta)
            self.pi_telemetery.update()
            self.autopilot.update()

            self.clock.tick(60)

    def quit(self):
        self.pi_telemetery.close()
        sys.exit()


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
