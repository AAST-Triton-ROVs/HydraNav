from loguru import logger
from logger.log_levels import LogLevels

__exports__ = ["logging", "LogLevels"]


class Logging:
    def __init__(self, max_messages: int = 20) -> None:
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
        self.set_level(LogLevels[level.upper()])

    def get_messages(self) -> list[str]:
        return self.__messages[-self.__max_messages :]

    def __handler(self, message: str) -> None:
        self.__messages.append(message.strip())


logging = Logging()
