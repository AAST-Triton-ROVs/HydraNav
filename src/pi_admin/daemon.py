import threading
from typing import Tuple
from pi_admin.enums import AdminCommands
from core.logger import system_logger
from threading import Thread
from queue import Queue
import socket
import time
import struct

SOCKET_TIMEOUT = 1.0

class PiAdminDaemon(Thread):
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
        admin_queue: Queue[AdminCommands],
        address: Tuple[str, int],
        quit_event: threading.Event,
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
        super().__init__(daemon=True)
        self.__admin_queue = admin_queue
        self.__quit_event = quit_event

        self.__address = address
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(SOCKET_TIMEOUT)
        self.server_socket.bind(self.__address)

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
                system_logger.info(f"Admin daemon accepted connection from {address}")
            except socket.timeout:
                system_logger.debug("Admin daemon no connection")
            if not self.__admin_queue.empty():
                command = self.__admin_queue.get()
                data = struct.pack("!I", command.value)
                try:
                    connection.send(data)
                except socket.error as e:
                    system_logger.error(f"Admin daemon failed with error: {e}")
