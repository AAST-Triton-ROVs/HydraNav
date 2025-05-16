from typing import Any, Callable, Dict
from core.logger_mixin import LoggerMixin

class Event:
    """
    An event representation.

    :param event_type: The type of the event.
    :type event_type: str
    :param data: Optional data associated with the event.
    :type data: Any
    """
    def __init__(self, event_type: str, data: Any = None):
        self.event_type: str = event_type
        self.data: Any = data


class EventDispatcher(LoggerMixin):
    """
    A dispatcher for events that allows listeners to subscribe, unsubscribe,
    and receive events when they are dispatched.
    """
    def __init__(self):
        """
        Initialize a new EventDispatcher instance with an empty listeners registry.
        """
        super().__init__()
        self.listeners: Dict[str, list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        """
        Subscribe a listener to a specific event type.

        :param event_type: The type of event to subscribe to.
        :type event_type: str
        :param listener: The listener function that will be called with the event data when the event is triggered.
        :type listener: Callable[[Any], None]
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: Callable):
        """
        Unsubscribe a listener from a specific event type.

        :param event_type: The type of event to unsubscribe from.
        :type event_type: str
        :param listener: The listener function to remove from the subscription list.
        :type listener: Callable[[Any], None]
        """
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)

    def dispatch(self, event: Event | str, data: Any = None):
        """
        Dispatch an event to all registered listeners.

        :param event: The event to dispatch, which can be an instance of Event or a string representing the event type.
        :type event: Event | str
        :param data: Optional data to associate with the event if the event is provided as a string.
        :type data: Any
        """
        if isinstance(event, str):
            event = Event(event, data)

        if event.event_type in self.listeners:
            for listener in self.listeners[event.event_type]:
                try:
                    listener(event.data)
                except Exception as e:
                    self._logger.critical(f"'{listener}' produced an error: {e}")

event_dispatcher = EventDispatcher()