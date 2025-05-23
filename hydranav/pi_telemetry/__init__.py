import queue
import multiprocessing
from multiprocessing import Queue
from hydranav.pi_telemetry.data import TelemetryData
from hydranav.pi_telemetry.daemon import TelemetryDaemon
from hydranav.core import event_dispatcher, GCSModule, Updatable, HasWebGUI
from nicegui import ui

__all__ = ["PiTelemetry", "TelemetryData"]


class PiTelemetry(GCSModule, Updatable):
    """
    A class for handling telemetry data via a queue and threading.

    :param dispatcher: The event dispatcher used for broadcasting telemetry events.
    :type dispatcher: EventDispatcher
    :param host: The host address to bind the telemetry daemon.
    :type host: str
    :param port: The port to bind the telemetry daemon.
    :type port: int
    """

    def __init__(self):
        """
        Constructor method that sets up the telemetry daemon and queue.

        :param dispatcher: The event dispatcher used for broadcasting telemetry events.
        :type dispatcher: EventDispatcher
        :param host: The host address to bind the telemetry daemon.
        :type host: str
        :param port: The port to bind the telemetry daemon.
        :type port: int
        """
        super().__init__()

        self.__queue: Queue = Queue(1)

        self.__quit_event = multiprocessing.Event()
        self.__listener_daemon = TelemetryDaemon(
            self.__queue,
            self.__quit_event,
        )
        self.__listener_daemon.start()

    def quit(self):
        self.__quit_event.set()
        self.__listener_daemon.join()

    def status_ok(self) -> bool:
        return self.__listener_daemon.is_alive()

    def update(self):
        """
        Retrieve telemetry data from the queue and dispatch it.

        :raises queue.Empty: If the queue is empty.
        """
        try:
            received_data: TelemetryData = self.__queue.get(block=False)
        except queue.Empty:
            return
        else:
            event_dispatcher.dispatch("telemetry", received_data)

    def close(self):
        """
        Close the listener thread's connection, releasing allocated resources.
        """
        self.__listener_daemon.close_connection()
