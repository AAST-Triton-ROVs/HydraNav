import logging
from typing import cast

import colorlog

SUCCESS_LEVEL = logging.INFO + 5
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
LOG_LEVELS = logging.getLevelNamesMapping()
PARENT_LOGGER_NAME = "HydraNav"


class CustomLogger(logging.Logger):
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, message, args, **kwargs)


logging.setLoggerClass(CustomLogger)


class ContextFilter(logging.Filter):
    def __init__(self, name=""):
        super().__init__(name)

    def filter(self, record):
        split_name = record.name.split(".")
        if split_name[0] == PARENT_LOGGER_NAME:
            record.name = split_name[1]

        return super().filter(record)


LOGGING_FORMATTER = colorlog.ColoredFormatter(
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


def create_logging_handler():
    handler = logging.StreamHandler()
    handler.addFilter(ContextFilter())
    handler.setFormatter(LOGGING_FORMATTER)
    return handler


class LoggerMixin:
    _parent_logger = logging.getLogger(PARENT_LOGGER_NAME)

    def __init__(self):
        class_name = self.__class__.__name__
        self._logger = cast(
            CustomLogger, logging.getLogger(f"{PARENT_LOGGER_NAME}.{class_name}")
        )

        if not self._logger.handlers:
            handler = create_logging_handler()
            self._logger.addHandler(handler)
            self._logger.propagate = False

    @classmethod
    def set_universal_logging_level(cls, level: str | int):
        if isinstance(level, str):
            cls._parent_logger.setLevel(LOG_LEVELS[level.upper()])
        else:
            cls._parent_logger.setLevel(level)
