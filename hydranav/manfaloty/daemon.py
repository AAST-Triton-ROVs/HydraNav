import multiprocessing
import queue
import socket
import struct
from core import config_manager, LoggerMixin
import time

RETRY_DELAY = 2
SOCKET_TIMEOUT = 1.0
BASE_IP = config_manager.get("networking", "baseIP")
PI_IP = config_manager.get("networking", "raspIP")
PORT = config_manager.get("manfaloty", "port")


class ManfalotyDaemon(multiprocessing.Process, LoggerMixin):
    """
    A daemon thread responsible for sending commands to the Manfaloty system.
    This thread continuously checks if any commands are available in the command queue.
    When a command is found, it is packed and sent to the specified address. Errors
    encountered during socket communication are logged, and automatic reconnection
    attempts are made after a delay if needed.

    :param server_socket: The socket used for transmitting command data.
    :type server_socket: socket.socket
    :param command_queue: A queue holding commands to be sent to the target system.
    :type command_queue: Queue[ManfalotyCommands]
    :param pi_ip: The IP address of the Manfaloty system.
    :type pi_ip: str
    :param port: The port on which the Manfaloty system is listening.
    :type port: int
    """

    def __init__(
        self,
        command_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        multiprocessing.Process.__init__(self, daemon=True)
        LoggerMixin.__init__(self)

        self.__address = BASE_IP, PORT
        self.__pi_address = PI_IP, PORT
        self.__server_socket = self.__create_socket()
        self.__quit_event = quit_event
        self.__command_queue = command_queue

    def __create_socket(self) -> socket.socket:
        """
        Binds the socket to the address.

        :raises socket.error: On socket failure
        """
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.settimeout(SOCKET_TIMEOUT)
                server_socket.setblocking(False)
                server_socket.bind(self.__address)
            except Exception as e:
                self._logger.error(f"Manfaloty daemon bounding error: {e}, retrying")
                time.sleep(RETRY_DELAY)
                continue

            self._logger.success(
                f"Manfaloty daemons bound to {self.__address[0]}:{self.__address[1]}"
            )
            return server_socket

    def run(self):
        while not self.__quit_event.is_set():
            try:
                command = self.__command_queue.get(block=False)
            except queue.Empty:
                self._logger.debug("Manfaloty daemon no new commands")
                continue

            try:
                data = struct.pack("!i", command.value)
            except struct.error as e:
                self._logger.critical(f"Manfaloty daemon packing error: {e}")
                continue

            try:
                self.__server_socket.sendto(data, self.__pi_address)
            except socket.timeout:
                self._logger.warning("Manfaloty client not connected")
                continue
            except BlockingIOError:
                self._logger.warning("OS networking buffer full")
                continue
            except Exception as e:
                self._logger.error(f"Manfaloty daemon error: {e}")
                continue

            self._logger.success(
                f"Sent {command.value} to {self.__pi_address[0]}:{self.__pi_address[1]}"
            )
