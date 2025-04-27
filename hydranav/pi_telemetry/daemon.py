import multiprocessing.synchronize
import queue
import struct
import socket
import multiprocessing
import time
from core.logger import system_logger
from core import config_manager
from pi_telemetry.data import TelemetryData

BUFFER_SIZE = struct.calcsize("!" + "I" * 7)
RECONNECT_DELAY = config_manager.get("networking", "retryDelaySec")
SOCKET_TIMEOUT = config_manager.get("networking", "socketTimeout")
HOST = config_manager.get("networking", "baseIP")
PORT = config_manager.get("piTelemetry", "port")


class TelemetryDaemon(multiprocessing.Process):
    """
    A daemon thread for receiving telemetry data packets over UDP.

    :param queue: A thread-safe queue to store incoming `TelemetryData`.
    :type queue: queue.Queue
    :param base_ip: IP address to bind to.
    :type base_ip: str
    :param port: UDP port to bind to.
    :type port: int
    """

    def __init__(
        self,
        queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        super().__init__(daemon=True)
        self.address = (HOST, PORT)
        self.server_socket = self.__create_socket()
        self.queue = queue
        self.__quit_event = quit_event

    def __create_socket(self) -> socket.socket:
        """
        Bind the server socket to the specified address.

        Attempts to create and bind a UDP socket to ``self.address``.
        If successful, logs a success message. If an error occurs,
        logs an error and retries after ``RECONNECT_DELAY``.

        :raises socket.error: If there is an error during socket creation or binding.
        """
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.settimeout(SOCKET_TIMEOUT)
                server_socket.bind(self.address)
            except Exception as e:
                system_logger.error(f"Telemetry daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)
                continue

            system_logger.success(
                f"Telemetry daemon bound to {self.address[0]}:{self.address[1]}"
            )
            return server_socket

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
        while not self.__quit_event.is_set():
            try:
                data, client = self.server_socket.recvfrom(BUFFER_SIZE)  # type: ignore
                system_logger.info(f"Telemetry data packet recieved from {client}")
            except socket.timeout:
                system_logger.debug("No new telemetry data")
                continue
            except Exception as e:
                system_logger.error(f"Telemetry daemon socket error: {e}")
                self.close_connection()
                self.__create_socket()
                continue

            unpacked_data = struct.unpack("!" + "I" * 5, data)
            telemetry_data = TelemetryData(
                unpacked_data[0],
                unpacked_data[1],
                unpacked_data[2],
                unpacked_data[3],
                unpacked_data[4],
            )
            system_logger.info(f"Recieved telemetry packet: {telemetry_data}")

            try:
                self.queue.put(
                    data,
                    block=False,
                )
            except queue.Full:
                system_logger.error("Unable to put telemetry data in queue")
                return
