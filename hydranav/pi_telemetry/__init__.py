import queue
import multiprocessing
from multiprocessing import Queue
from hydranav.core.has_webgui import HasWebGUI
from hydranav.pi_telemetry.data import TelemetryData
from hydranav.pi_telemetry.daemon import TelemetryDaemon
from hydranav.core import event_dispatcher, GCSModule, Updatable
import random
import time
from nicegui import ui

__all__ = ["PiTelemetry", "TelemetryData"]


class PiTelemetry(GCSModule, Updatable, HasWebGUI):
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

        self.__queue: multiprocessing.Queue[TelemetryData] = Queue(1)
        self.__ui_queue: multiprocessing.Queue[TelemetryData] = Queue(1)

        self.__quit_event = multiprocessing.Event()
        self.__listener_daemon = TelemetryDaemon(
            self.__queue,
            self.__quit_event,
        )
        self.__listener_daemon.start()

    @classmethod
    def init_order(cls):
        return 1

    def webgui_contents(self):
        container = ui.column(align_items="center").classes("w-full")
        with container:
            with ui.card().classes("w-1/2 justify-center items-center"):
                ui.label("Pi Telemetry").classes(
                    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
                )
                table = ui.table(
                    columns=[
                        {
                            "name": "metric",
                            "label": "Metric",
                            "field": "metric",
                            "align": "center",
                        },
                        {
                            "name": "value",
                            "label": "Value",
                            "field": "value",
                            "align": "center",
                        },
                    ],
                    rows=[
                        {"metric": "CPU Usage", "value": "N/A%"},
                        {"metric": "CPU Temp", "value": "N/A°C"},
                        {"metric": "RAM Usage", "value": "N/A%"},
                        {"metric": "Disk Usage", "value": "N/A%"},
                        {"metric": "GPU Temp", "value": "N/A°C"},
                        {"metric": "Voltage", "value": "N/AV"},
                    ],
                ).classes("w-full")

        def update_table():
            try:
                data = self.__ui_queue.get(block=False)
            except queue.Empty:
                return

            table.rows.clear()
            table.rows.extend(
                [
                    {"metric": "CPU Usage", "value": f"{data.cpu_usage:>5} %"},
                    {"metric": "CPU Temp", "value": f"{data.cpu_temp:>5} °C"},
                    {"metric": "RAM Usage", "value": f"{data.ram_usage:>5} %"},
                    {"metric": "Disk Usage", "value": f"{data.disk_usage:>5} %"},
                    {"metric": "GPU Temp", "value": f"{data.gpu_temp:>5} °C"},
                    {"metric": "Voltage", "value": f"{data.voltage:>5.2f} V"},
                ]
            )
            table.update()

        ui.timer(0.8, update_table)
        return container

    def webgui_icon_name(self):
        return "insights"

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
            data = self.__queue.get(block=False)
        except queue.Empty:
            return
        else:
            event_dispatcher.dispatch("telemetry", data)

        try:
            self.__ui_queue.put(data, block=False)
        except queue.Full:
            return

    def close(self):
        """
        Close the listener thread's connection, releasing allocated resources.
        """
        self.__listener_daemon.close_connection()
