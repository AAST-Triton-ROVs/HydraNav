import sys
import pygame
import argparse
from core.module_manager import ModuleManager
from core.logger import system_logger, LogLevels
from core.request_manager import RequestManager
from user_input import UserInput
from core.event_dispatcher import EventDispatcher
from gui import GUI
from manfaloty import Manfaloty
from notifier import Notifier
from pi_telemetry import PiTelemetery
from pi_admin import PiAdmin
from autopilot import Autopilot

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
        self.dispatcher = EventDispatcher()
        self.request_manager = RequestManager()
        self.module_manager = ModuleManager(self.dispatcher)

        self.user_input = UserInput(self.dispatcher, self.request_manager)
        self.module_manager.register_module(self.user_input)

        if not self.companion_mode:
            self.autopilot = Autopilot(self.dispatcher)
            self.module_manager.register_module(self.autopilot)
            
            self.notifier = Notifier(self.dispatcher, self.request_manager)
            self.module_manager.register_module(self.notifier)

        self.pi_telemetery = PiTelemetery(self.dispatcher)
        self.module_manager.register_module(self.pi_telemetery)

        self.admin = PiAdmin(self.request_manager)
        self.module_manager.register_module(self.admin)
        
        self.manfaloty = Manfaloty(self.dispatcher, self.request_manager)
        self.module_manager.register_module(self.manfaloty)

        system_logger.info(f"Loaded modules: {' '.join(self.module_manager.loaded_modules)}")
        self.user_input.controller.update_connection_status()

    def run(self):
        while True:
            # time_delta = (
            #     self.clock.tick(60) / 1000.0
            # )  # .tick return the time sinze last frame in milliseconds so we must divide it by 1000.0

            # self.gui.update(time_delta)
            self.user_input.update()
            self.pi_telemetery.update()
            self.manfaloty.update()

            if not self.companion_mode:
                self.autopilot.update()

            self.clock.tick(60)


if __name__ == "__main__":
    gcs = GCS()
    gcs.run()
