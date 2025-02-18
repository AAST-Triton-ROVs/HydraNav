from loguru import logger


class Logging:
    def __init__(self, max_messages: int = 20, level: str = "DEBUG") -> None:
        self.__max_messages: int = max_messages
        self.__messages: list[str] = [""] * self.__max_messages

        self.logger = logger
        self.logger.add(
            self.__handler, format="{time:HH:mm:ss} | {level} | {message}", level=level
        )
        self.logger.add(
            "gcs.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function} | {message}",
            level=level,
            mode="w",
        )

    def get_messages(self) -> list[str]:
        return self.__messages[-self.__max_messages :]

    def __handler(self, message: str) -> None:
        self.__messages.append(message.strip())


logging = Logging()
