from loguru import logger
from logger.log_levels import LogLevels

__exports__ = ["logging", "LogLevels"]


class Logging:
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
        self.logger.add(self.__handler, format="{time:HH:mm:ss} | {level} | {message}")
        self.logger.add(
            "gcs.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function} | {message}",
            mode="w",
        )

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

        self.logger.add(
            self.__handler,
            format="{time:HH:mm:ss} | {level} | {message}",
            level=level.value,
        )
        self.logger.add(
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

    def __handler(self, message: str) -> None:
        self.__messages.append(message.strip())


logging = Logging()
