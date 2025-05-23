from abc import ABC, abstractmethod
from hydranav.core.logger import LoggerMixin


class GCSModule(ABC, LoggerMixin):
    def __init__(self):
        super().__init__()

    @classmethod
    def module_name(cls):
        """Returns Module name"""
        return cls.__name__

    @abstractmethod
    def quit(self):
        """Quits module"""
        ...

    @abstractmethod
    def status_ok(self) -> bool:
        """Returns status of module

        Returns:
            bool: status, True is active and False if not
        """
        ...
