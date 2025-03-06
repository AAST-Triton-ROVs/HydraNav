import sys
from typing import Optional
from loguru import logger
from logger.log_levels import LogLevels

__all__ = ["logging", "LogLevels"]


class SystemLogger:
    """
    The Logging class provides a simple interface for storing and managing log messages in a ring buffer.
    It uses the loguru package to configure both console and file logging.

    :param max_messages: The maximum number of log messages to store in memory.
    :type max_messages: int
    :default max_messages: 20
    """

    def __init__(self, max_messages: int = 20) -> None:
        """
        Initialize the logger.

        :param max_messages: The maximum number of messages to retain.
        :type max_messages: int
        """

        self.__max_messages: int = max_messages
        self.__messages: list[str] = [""] * self.__max_messages

        self.logger = logger

        self.__stderr_handler: Optional[int] = self.logger.add(
            sys.stderr, level="ERROR", backtrace=True, diagnose=True
        )
        self.__custom_handler: Optional[int] = None
        self.__file_handler: Optional[int] = None
        self.__stdout_handler: Optional[int] = None

    def set_level(self, level: LogLevels):
        """
        Set the log level for the logger.
        Removes any existing handlers and adds a new console and file handler with
        the specified logging level.

        :param level: An instance of the LogLevels enum specifying the logging level.
        :type level: LogLevels
        :returns: None
        :rtype: None
        """

        self.logger.remove()

        self.__custom_handler = self.logger.add(
            self.__handler,
            format="{time:HH:mm:ss} | {level} | {message}",
            level=level.value,
        )
        self.__stdout_handler = self.logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
            colorize=True,
            level=level.value,
        )
        self.__file_handler = self.logger.add(
            "gcs.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function} | {message}",
            level=level.value,
            mode="w",
        )

    def set_level_str(self, level: str):
        """
        Set the logging level using a string value.

        :param level: The desired logging level name. The value must be a valid key in ``LogLevels``.
        :type level: str
        :raises KeyError: If the specified logging level does not exist in ``LogLevels``.
        """

        self.set_level(LogLevels[level.upper()])

    def get_messages(self) -> list[str]:
        """
        Return the stored messages, up to the maximum allowed.

        :returns: A list of the stored messages.
        :rtype: list[str]
        """

        return self.__messages[-self.__max_messages :]

    def trace(self, message: str) -> None:
        self.logger.trace(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def success(self, message: str) -> None:
        self.logger.success(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)

    def __handler(self, message: str) -> None:
        self.__messages.append(message.strip())


system_logger = SystemLogger()
