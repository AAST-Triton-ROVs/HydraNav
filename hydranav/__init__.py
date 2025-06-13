import argparse
from hydranav.core import config_manager, module_manager, LoggerMixin, TTS, LOG_LEVELS

# from gui import GUI
from hydranav.keyboard_input import KeyboardInput
from hydranav.controller_input import ControllerInput
from hydranav.manfaloty import Manfaloty
from hydranav.pi_admin import PiAdmin
from hydranav.autopilot import Autopilot
from hydranav.pi_telemetry import PiTelemetry
from hydranav.vision.streaming import CameraStreamer
from hydranav.web_gui import WebGUI

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

        LoggerMixin.set_universal_logging_level(args.loglevel)
        self._logger.info(f"Log level set to {args.loglevel.upper()}")

        self.companion_mode = args.companion
        self._logger.info(
            f"Operating mode: {'Companion' if self.companion_mode else 'Normal'}"
        )

        TTS.init()
        TTS.update_and_generate_lines()

        module_manager.init_modules(
            [
                ControllerInput,
                PiTelemetry,
                PiAdmin,
                Manfaloty,
                CameraStreamer,
                # KeyboardInput,
            ]
        )

        if not self.companion_mode:
            module_manager.init_modules(
                [
                    # Autopilot,
                    WebGUI,
                ]
            )
        else:
            TTS.disable()

        self._logger.info(f"Loaded modules: {' '.join(module_manager.loaded_modules)}")

    def run(self):
        while True:
            module_manager.update_all()
