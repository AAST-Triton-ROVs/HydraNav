import sys
import pygame
from logger import logging, LogLevels
from user_input import UserInput
from events import EventDispatcher
from gui import GUI
from manfaloty import Manfaloty
from notifier import Notifier
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
    parser.add_argument(
        "-l",
        "--log-level",
        choices=[level.value.lower() for level in LogLevels],
        default=LogLevels.INFO,
        help="Set the log level"
    )
    return parser


class GCS:
    def __init__(self):
        pygame.init()

        parser = init_parser()
        args = parser.parse_args()

        self.log_level: str = args.log_level
        logging.logger.info(f"Log mode set to {self.log_level.upper()}")
        logging.set_level_str(self.log_level)
        
        self.companion_mode = args.companion
        logging.logger.info(f"Operating mode: {'Companion' if self.companion_mode else 'Normal'}")
        

        self.clock = pygame.time.Clock()
        self.dispatcher = EventDispatcher()

        # self.gui = GUI(self.dispatcher, self.logging)
        self.user_input = UserInput(self.dispatcher)
        if not self.companion_mode:
            self.notifier = Notifier(self.dispatcher)

        self.pi_telemetery = PiTelemetery(self.dispatcher)

        if not self.companion_mode:
            self.autopilot = Autopilot(self.dispatcher)

        self.manfaloty = Manfaloty(self.dispatcher)

        self.user_input.controller.update_connection_status()
        
    def run(self):
        while True:
            # time_delta = (
            #     self.clock.tick(60) / 1000.0
            # )  # .tick return the time sinze last frame in milliseconds so we must divide it by 1000.0

            # self.gui.update(time_delta)
            self.user_input.controller.update()
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
