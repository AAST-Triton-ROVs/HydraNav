from typing import Any, Callable, Dict


class Event:
    def __init__(self, event_type: str, data: Any = None):
        self.event_type: str = event_type
        self.data: Any = data


class EventDispatcher:
    def __init__(self):
        self.listeners: Dict[str, list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        if event_type not in self.listeners:
            self.listeners[event_type] = []

        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: Callable):
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)

    def dispatch(self, event: Event | str, data: Any = None):
        if isinstance(event, str):
            event = Event(event, data)

        if event.event_type in self.listeners:
            for listener in self.listeners[event.event_type]:
                listener(event.data)
