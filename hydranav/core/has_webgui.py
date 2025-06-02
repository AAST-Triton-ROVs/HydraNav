from abc import ABC, abstractmethod
from nicegui import ui


class HasWebGUI(ABC):
    @abstractmethod
    def webgui_contents(self) -> ui.element: ...

    @abstractmethod
    def webgui_icon_name(self) -> str: ...
