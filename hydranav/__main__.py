import pygame
import argparse
from core import config_manager, system_logger, LogLevels, module_manager
from user_input import UserInput
from gui import GUI
from manfaloty import Manfaloty
from notifier import Notifier
from pi_admin import PiAdmin
from autopilot import Autopilot
from pi_telemetry import PiTelemetry

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
        config_manager.init()

        parser = init_parser()
        args = parser.parse_args()

        system_logger.set_level_str(args.loglevel)
        system_logger.info(f"Log level set to {args.loglevel.upper()}")

        self.companion_mode = args.companion
        system_logger.info(
            f"Operating mode: {'Companion' if self.companion_mode else 'Normal'}"
        )

        self.clock = pygame.time.Clock()

        module_manager.init_modules([UserInput, PiTelemetry, PiAdmin, Manfaloty])

        if not self.companion_mode:
            module_manager.init_modules([Autopilot, Notifier])

        system_logger.info(f"Loaded modules: {' '.join(module_manager.loaded_modules)}")
        module_manager.UserInput.controller.update_connection_status()

    def run(self):
        while True:
            module_manager.update_all()

            system_logger.trace(str(self.clock.get_fps()))

            self.clock.tick(60)


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
