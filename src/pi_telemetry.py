from dataclasses import dataclass
import struct
import queue
import socket
from threading import Thread
import time
from typing import Optional, Tuple
from events import EventDispatcher
from logger import Logging

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
        self.__queue: queue.Queue = queue.Queue()

        self.__listener_thread = TelemetryListener(
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


class TelemetryListener(Thread):
    def __init__(self, logging: Logging, queue: queue.Queue, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.logging = logging
        self.queue = queue
        self.daemon = True

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                self.server_socket.bind((self.host, self.port))
                break
            except OSError:
                self.logging.logger.error(
                    f"Telemetery cannot bind socket to {self.host}:{self.port}, retrying"
                )
                time.sleep(1)
                
        self.server_socket.listen()
        self.logging.logger.info(
            f"Telemetery server listening on {self.host}:{self.port}"
        )

        buffer_size = struct.calcsize("i" * 8)
        while True:
            connection, addr = self.server_socket.accept()
            self.logging.logger.debug(f"Telemetery accepted connection from {addr[0]}")

            data = connection.recv(buffer_size)
            self.logging.logger.info("Telemetry data packet recieved")

            unpacked_data = struct.unpack("i" * 8, data)
            self.queue.put(
                TelemeteryData(
                    unpacked_data[0],
                    unpacked_data[1],
                    unpacked_data[2],
                    unpacked_data[3],
                    unpacked_data[4],
                    unpacked_data[5],
                    (unpacked_data[6], unpacked_data[7]),
                )
            )

            data = connection.recv(buffer_size)
                
                
            
@dataclass
class TelemeteryData:
    cpu_usage: int
    cpu_temp: int
    ram_usage: int
    disk_usage: int
    gpu_usage: int
    gpu_temp: int
    network_usage: Tuple[int, int]
