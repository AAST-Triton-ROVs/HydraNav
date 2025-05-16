from enum import IntEnum
import logging
from typing import cast

import colorlog

SUCCESS_LEVEL = logging.INFO + 5
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class CustomLogger(logging.Logger):
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, message, args, **kwargs)


logging.setLoggerClass(CustomLogger)

LOG_LEVELS = logging.getLevelNamesMapping()


class LoggerMixin:
    _logging_level = LOG_LEVELS["INFO"]

    def __init__(self):
        class_name = self.__class__.__name__
        self._logger = cast(CustomLogger, logging.getLogger(class_name))
        self._logger.setLevel(self._logging_level)

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = colorlog.ColoredFormatter(
                fmt="%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-18s | %(message)s",
                datefmt="%I:%M:%S %p",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "white",
                    "SUCCESS": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red,bg_white",
                },
                style="%",
            )

            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.propagate = False

    @classmethod
    def set_default_logging_level(cls, level: str):
        if level not in LOG_LEVELS:
            raise ValueError(
                f"{level} is not a valid level; valid levels are [{' '.join(LOG_LEVELS.keys())}]"
            )

        cls._logging_level = LOG_LEVELS[level]

    @classmethod
    def get_logging_level(cls) -> str:
        reversed_log_levels = {v: k for k, v in LOG_LEVELS.items()}
        return reversed_log_levels[cls._logging_level]
