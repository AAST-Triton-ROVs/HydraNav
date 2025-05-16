import pygame
import argparse
from core import config_manager, module_manager, LoggerMixin, TTS, LOG_LEVELS

# from user_input import UserInput
# from gui import GUI
# from notifier import Notifier
from manfaloty import Manfaloty
from pi_admin import PiAdmin

# from autopilot import Autopilot
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
        choices=[level.lower() for level in LOG_LEVELS.keys()],
        type=str,
        default="info",
    )
    return parser


class GCS(LoggerMixin):
    def __init__(self, args):
        super().__init__()

        LoggerMixin.set_default_logging_level(args.loglevel.upper())
        self._logger.info(f"Log level set to {args.loglevel.upper()}")

        self.companion_mode = args.companion
        self._logger.info(
            f"Operating mode: {'Companion' if self.companion_mode else 'Normal'}"
        )

        TTS.init()
        TTS.update_and_generate_lines()

        module_manager.init_modules(
            [
                UserInput,
                PiTelemetry,
                PiAdmin,
                Manfaloty,
            ]
        )

        if not self.companion_mode:
            module_manager.init_modules(
                [
                    Autopilot,
                ]
            )

        self._logger.info(f"Loaded modules: {' '.join(module_manager.loaded_modules)}")

    def run(self):
        while True:
            module_manager.update_all()


if __name__ == "__main__":
    parser = init_parser()
    args = parser.parse_args()
    gcs = GCS(args)
    gcs.run()
