import queue
import struct
import socket
from threading import Thread
import time
from typing import Optional
from logger import Logging
from pi_telemetry.data import TelemeteryData

class TelemetryListener(Thread):
    def __init__(self, logging: Logging, queue: queue.Queue, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.logging = logging
        self.queue = queue

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
           