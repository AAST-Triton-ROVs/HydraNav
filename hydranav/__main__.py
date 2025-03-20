import sys
import pygame
import argparse
from core import ModuleManager
from user_input import UserInput
from gui import GUI
from manfaloty import Manfaloty
from notifier import Notifier
from pi_telemetry import PiTelemetry
from pi_admin import PiAdmin
from autopilot import Autopilot
from core import system_logger, LogLevels

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
        "--loglevel",
        help="Set the logging level",
        choices=[level.name.lower() for level in LogLevels],
        type=str,
        default="info",
    )
    return parser


class GCS:
    def __init__(self):
        pygame.init()

        parser = init_parser()
        args = parser.parse_args()

        system_logger.set_level_str(args.loglevel)
        system_logger.info(f"Log level set to {args.loglevel.upper()}")

        self.companion_mode = args.companion
        system_logger.info(
            f"Operating mode: {'Companion' if self.companion_mode else 'Normal'}"
        )

        self.clock = pygame.time.Clock()
        self.module_manager = ModuleManager()

        self.user_input = UserInput()
        self.pi_telemetry = PiTelemetry()
        self.admin = PiAdmin()
        self.manfaloty = Manfaloty()
        self.module_manager.register_modules(
            [
                self.user_input,
                self.pi_telemetry,
                self.admin,
                self.manfaloty,
            ]
        )

        if not self.companion_mode:
            self.autopilot = Autopilot()
            self.notifier = Notifier()
            self.module_manager.register_modules([self.notifier, self.autopilot])

        system_logger.info(
            f"Loaded modules: {' '.join(self.module_manager.loaded_modules)}"
        )
        self.user_input.controller.update_connection_status()

    def run(self):
        while True:
            # time_delta = (
            #     self.clock.tick(60) / 1000.0
            # )  # .tick return the time sinze last frame in milliseconds so we must divide it by 1000.0

            # self.gui.update(time_delta)
            self.user_input.update()
            self.pi_telemetry.update()
            self.manfaloty.update()

            if not self.companion_mode:
                self.autopilot.update()

            self.clock.tick(60)


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
