import queue
from queue import Queue
from events import EventDispatcher
from logger import Logging
from pi_telemetry.data import TelemeteryData
from pi_telemetry.daemon import TelemetryDaemon

__exports__ = ["Telemetery", "TelemeteryData"]


class PiTelemetery:
    def __init__(
        self,
        dispatcher: EventDispatcher,
        logging: Logging,
        host: str = "0.0.0.0",
        port=2500,
    ):
        self.__dispatcher = dispatcher
        self.__logging = logging
        self.__host = host
        self.__port = port
        self.__queue: Queue = Queue(1)

        self.__listener_thread = TelemetryDaemon(
            self.__logging, self.__queue, self.__host, self.__port
        )
        self.__listener_thread.start()

    def update(self):
        try:
            recieved_data: TelemeteryData = self.__queue.get(block=False)
        except queue.Empty:
            return
        else:
            self.__dispatcher.dispatch("telemetery", recieved_data)

    def close(self):
        self.__listener_thread.close_connection()

     
