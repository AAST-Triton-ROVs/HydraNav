from typing import Any, Callable, Dict
from hydranav.core.logger import LoggerMixin


class RequestManager(LoggerMixin):
    """
    Manages requests and their associated handlers.
    """

    def __init__(self):
        """
        Initializes a new instance of the RequestManager, with an empty request handlers registery
        """
        super().__init__()
        self.request_handlers: Dict[str, list[Callable]] = {}

    def register_handler(self, name: str, handler: Callable):
        """
        Registers a handler for a specific request name if one does not already exist.

        :param name: The name of the request to register.
        :type name: str
        :param handler: The callable that will handle the request.
        :type handler: Callable
        :return: None
        :rtype: None
        """
        if self.request_handlers.get(name) is None:
            self.request_handlers[name] = []

        self.request_handlers[name].append(handler)
        self._logger.debug(f"{handler} registered to {name}")

    def remove_request(self, name: str):
        """
        Removes the handler associated with a given request name.

        :param name: The name of the request to remove.
        :type name: str
        :return: None
        :rtype: None
        """
        if self.request_handlers.get(name):
            self._logger.debug(f"{self.request_handlers[name]} unregistered to {name}")
            del self.request_handlers[name]

    def request(self, name: str, *args, **kwargs) -> list[Any]:
        """
        Invokes the handlers for the specified request name with the provided arguments.
        :param name: The name of the request to be invoked.
        :type name: str
        :param args: Positional arguments to pass to the handler.
        :param kwargs: Keyword arguments to pass to the handler.
        :return: None if the request name does not have a corresponding handler.
        :rtype: None
        """
        if not self.request_handlers.get(name):
            return []

        self._logger.debug(
            f"{name} is being requested, calling {self.request_handlers[name]}"
        )
        output = []
        for handler in self.request_handlers[name]:
            output.append(handler(*args, **kwargs))

        return output


request_manager = RequestManager()
