from typing import Any, Callable, Dict


class Event:
    def __init__(self, event_type: str, data: Any = None):
        self.event_type: str = event_type
        self.data: Any = data


class EventDispatcher:
    def __init__(self):
        self.listeners: Dict[str, list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        """
        Subscribe a listener to a specific event type.
        
        :param event_type: The type of event to subscribe to.
        :type event_type: str
        :param listener: The listener function to be called when the event is triggered.
        :type listener: Callable
        """
        
        if event_type not in self.listeners:
            self.listeners[event_type] = []

        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: Callable):
        """
        Unsubscribe a listener from a specific event type.
        
        :param event_type: The type of event to unsubscribe from.
        :type event_type: str
        :param listener: The listener to remove from the event's subscription list.
        :type listener: Callable
        """
        
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)

    def dispatch(self, event: Event | str, data: Any = None):
        """
        Dispatches an event to all registered listeners.
        
        :param event: The event to dispatch. Can be an instance of Event or a string representing the event type.
        :type event: Event | str
        :param data: Optional data to pass along with the event, defaults to None.
        :type data: Any, optional
        """
        
        if isinstance(event, str):
            event = Event(event, data)

        if event.event_type in self.listeners:
            for listener in self.listeners[event.event_type]:
                listener(event.data)
