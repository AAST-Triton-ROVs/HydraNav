import queue
import struct
import socket
from threading import Thread
import time
from typing import Optional
from logger import logging
from pi_telemetry.data import TelemetryData

BUFFER_SIZE = struct.calcsize("i" * 8)
RECONNECT_DELAY = 2


class TelemetryDaemon(Thread):
    def __init__(self, queue: queue.Queue, base_ip: str, port: int):
        super().__init__(daemon=True)
        self.address = (base_ip, port)
        self.server_socket: Optional[socket.socket] = None

        self.queue = queue

    def __bind_socket(self):
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.server_socket.bind(self.address)
                logging.logger.success(
                    f"Telemetry daemon bound to {self.address[0]}:{self.address[1]}"
                )
                return
            except socket.error as e:
                logging.logger.error(f"Telemetry daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()

    def run(self):
        self.__bind_socket()
        while True:
            try:
                data, client = self.server_socket.recvfrom(BUFFER_SIZE)  # type: ignore
                logging.logger.info(f"Telemetry data packet recieved from {client}")
            except socket.error as e:
                logging.logger.error(f"Telemetry daemon socket error: {e}")
                self.close_connection()
                self.__bind_socket()
                continue

            unpacked_data = struct.unpack("i" * 8, data)
            self.queue.put(
                TelemetryData(
                    unpacked_data[0],
                    unpacked_data[1],
                    unpacked_data[2],
                    unpacked_data[3],
                    unpacked_data[4],
                    unpacked_data[5],
                    (unpacked_data[6], unpacked_data[7]),
                )
            )
