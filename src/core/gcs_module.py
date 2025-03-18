from core.event_dispatcher import EventDispatcher
from core.request_manager import RequestManager
from abc import ABC, abstractmethod


class GCSModule(ABC):
    def __init__(self, dispatcher: EventDispatcher, request_manager: RequestManager):
        super().__init__()

        self._dispatcher = dispatcher
        self._request_manager = request_manager

    @abstractmethod
    def quit(self): ...

    def _quit_successful(self):
        self._dispatcher.dispatch("module_quit", type(self).__name__)
