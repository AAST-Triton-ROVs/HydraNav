from abc import ABC, abstractmethod
from event_dispatcher import EventDispatcher
from request_manager import RequestManager


class GCSModule(ABC):
    def __init__(self, dispatcher: EventDispatcher, request_manager: RequestManager):
        super().__init__()

        self.__dispatcher = dispatcher
        self.__request_manager = request_manager

    @abstractmethod
    def quit(self): ...
