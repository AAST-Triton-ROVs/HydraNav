import multiprocessing.synchronize
import queue
import multiprocessing
import socket
import struct
from hydranav.core import config_manager, LoggerMixin

SOCKET_TIMEOUT = config_manager["networking", "socketTimeout"]
BASE = config_manager["networking", "baseIP"]
PORT = config_manager["piAdmin", "port"]


class PiAdminDaemon(multiprocessing.Process, LoggerMixin):
    """
    A daemon thread for listening to admin commands.

    :param admin_queue:
        A queue holding admin commands.
    :type admin_queue: Queue[AdminCommands]
    :param address:
        A tuple containing the host address and port.
    :type address: Tuple[str, int]
    """

    def __init__(
        self,
        admin_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        """
        Initialize the daemon with an admin commands queue and a network address.

        :param admin_queue:
            A queue holding admin commands.
        :type admin_queue: Queue[AdminCommands]
        :param address:
            A tuple with the host and port.
        :type address: Tuple[str, int]
        """
        multiprocessing.Process.__init__(self, daemon=True)
        LoggerMixin.__init__(self)
        
        self.__admin_queue = admin_queue
        self.__quit_event = quit_event

        self.__address = (BASE, PORT)
        self.server_socket = self.__create_socket()

        self._logger.success(f"Admin daemon bound to {BASE}:{PORT}")

    def __create_socket(self) -> socket.socket:
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.settimeout(SOCKET_TIMEOUT)
                server_socket.bind(self.__address)
            except Exception as e:
                self._logger.error(f"PiAdmin daemon bounding error: {e}")
                continue

            return server_socket

    def run(self):
        """
        Listen for incoming connections and send admin commands.

        On accepting a connection, retrieve a command from the queue if available,
        pack the command value, and send it to the client.
        """
        self.server_socket.listen()
        while not self.__quit_event.is_set():
            try:
                connection, address = self.server_socket.accept()
            except socket.timeout:
                self._logger.debug("Admin daemon no connection")
                continue

            self._logger.success(f"Admin daemon accepted connection from {address}")
            try:
                command = self.__admin_queue.get(block=False)
            except queue.Empty:
                continue

            data = struct.pack("!I", command.value)
            try:
                connection.send(data)
            except Exception as e:
                self._logger.error(f"Admin daemon failed with error: {e}")
