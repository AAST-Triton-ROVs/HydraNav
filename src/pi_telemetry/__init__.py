import queue
from queue import Queue
from events import EventDispatcher
from pi_telemetry.data import TelemetryData
from pi_telemetry.daemon import TelemetryDaemon

__all__ = ["Telemetery", "TelemeteryData"]


class PiTelemetery:
    """
    A class for handling telemetry data via a queue and threading.

    :param dispatcher: The event dispatcher used for broadcasting telemetry events.
    :type dispatcher: EventDispatcher
    :param host: The host address to bind the telemetry daemon.
    :type host: str
    :param port: The port to bind the telemetry daemon.
    :type port: int
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        host: str = "0.0.0.0",
        port=2010,
    ):
        """
        Constructor method that sets up the telemetry daemon and queue.

        :param dispatcher: The event dispatcher used for broadcasting telemetry events.
        :type dispatcher: EventDispatcher
        :param host: The host address to bind the telemetry daemon.
        :type host: str
        :param port: The port to bind the telemetry daemon.
        :type port: int
        """
        self.__dispatcher = dispatcher
        self.__host = host
        self.__port = port
        self.__queue: Queue = Queue(1)

        self.__listener_thread = TelemetryDaemon(self.__queue, self.__host, self.__port)
        self.__listener_thread.start()

    def update(self):
        """
        Retrieve telemetry data from the queue and dispatch it.

        :raises queue.Empty: If the queue is empty.
        """
        try:
            recieved_data: TelemetryData = self.__queue.get(block=False)
        except queue.Empty:
            return
        else:
            self.__dispatcher.dispatch("telemetery", recieved_data)

    def close(self):
        """
        Close the listener thread's connection, releasing allocated resources.
        """
        self.__listener_thread.close_connection()
