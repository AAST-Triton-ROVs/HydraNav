import queue
import struct
import socket
from threading import Thread
import time
from typing import Optional
from core.logger import system_logger
from pi_telemetry.data import TelemetryData

BUFFER_SIZE = struct.calcsize("!" + "I" * 8)
RECONNECT_DELAY = 2


class TelemetryDaemon(Thread):
    """
    A daemon thread for receiving telemetry data packets over UDP.

    :param queue: A thread-safe queue to store incoming `TelemetryData`.
    :type queue: queue.Queue
    :param base_ip: IP address to bind to.
    :type base_ip: str
    :param port: UDP port to bind to.
    :type port: int
    """

    def __init__(self, queue: queue.Queue, base_ip: str, port: int):
        super().__init__(daemon=True)
        self.address = (base_ip, port)
        self.server_socket: Optional[socket.socket] = None
        self.queue = queue

    def __bind_socket(self):
        """
        Bind the server socket to the specified address.

        Attempts to create and bind a UDP socket to ``self.address``.
        If successful, logs a success message. If an error occurs,
        logs an error and retries after ``RECONNECT_DELAY``.

        :raises socket.error: If there is an error during socket creation or binding.
        """
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.server_socket.bind(self.address)
                system_logger.success(
                    f"Telemetry daemon bound to {self.address[0]}:{self.address[1]}"
                )
                return
            except socket.error as e:
                system_logger.error(f"Telemetry daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        """
        Close the server socket if it is open.

        Checks if ``server_socket`` is set and closes it if so.
        """

        if self.server_socket:
            self.server_socket.close()

    def run(self):
        """
        Continuously receive and process telemetry data packets.

        Binds the server socket, receives data packets from clients,
        unpacks them, and places them in the queue. If a socket error
        occurs, the connection is closed and re-established.

        :raises socket.error: If a socket error occurs.
        """
        self.__bind_socket()
        while True:
            try:
                data, client = self.server_socket.recvfrom(BUFFER_SIZE)  # type: ignore
                system_logger.info(f"Telemetry data packet recieved from {client}")
            except socket.error as e:
                system_logger.error(f"Telemetry daemon socket error: {e}")
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
                ),
            )
