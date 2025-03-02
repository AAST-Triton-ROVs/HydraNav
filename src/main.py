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
import argparse

DESCRIPTION = "HydraNav, a revolutionary Ground Control System (GCS) for underwater ROVs, providing seamless integration with various controllers, real-time telemetry, and advanced autopilot features."


def init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "-c",
        "--companion",
        help="Toggle companion mode",
        action="store_true",
    )
    return parser


class GCS:
    def __init__(self):
        pygame.init()

        parser = init_parser()
        args = parser.parse_args()
        self.companion_mode = args.companion

        self.clock = pygame.time.Clock()
        self.dispatcher = EventDispatcher()

        # self.gui = GUI(self.dispatcher, self.logging)
        self.controller = Controller(self.dispatcher)
        if not self.companion_mode:
            self.notifier = Notifier(self.dispatcher)

        self.pi_telemetery = PiTelemetery(self.dispatcher)

        if not self.companion_mode:
            self.autopilot = Autopilot(self.dispatcher)

        self.manfaloty = Manfaloty(self.dispatcher)

        self.controller.update_connection_status()

        self.dispatcher.subscribe(
            "controller_button",
            self.on_controller_button,
        )
        if not self.companion_mode:
            self.dispatcher.subscribe(
                "controller_joysticks",
                self.handle_controller_joysticks,
            )

    def handle_controller_joysticks(self, move: Tuple[float, float, float, float]):
        x, y, z, w = move

        self.autopilot.move(x, y, z, w, 0)

    def on_controller_button(self, button: str):
        if self.companion_mode:
            match button:
                case "L":
                    self.notifier.play("bolbol")
                case "M":
                    self.controller.calibrate()
                case "A":
                    self.autopilot.arm()
                case "B":
                    self.autopilot.disarm()

            return

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

            # self.gui.update(time_delta)
            self.controller.update()
            self.pi_telemetery.update()
            self.manfaloty.update()

            if not self.companion_mode:
                self.autopilot.update()

            self.clock.tick(60)

    def quit(self):
        self.pi_telemetery.close()
        sys.exit()


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
