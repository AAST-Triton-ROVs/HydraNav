from abc import ABC, abstractmethod


class GCSModule(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def quit(self): ...

    @abstractmethod
    def status_ok(self): ...
