import queue
import threading
from typing import Tuple
from threading import Thread
from queue import Queue
import socket
import time
import struct
from core import config_manager
from pi_admin.enums import AdminCommands
from core import system_logger

SOCKET_TIMEOUT = config_manager.get("networking", "socketTimeout")
BASE = config_manager.get("networking", "baseIP")
PORT = config_manager.get("piAdmin", "port")


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

        self.__address = (BASE, PORT)
        self.server_socket = self.__create_socket()

        system_logger.success(f"Admin daemon bound to {BASE}:{PORT}")

    def __create_socket(self) -> socket.socket:
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.settimeout(SOCKET_TIMEOUT)
                server_socket.bind(self.__address)
            except socket.error as e:
                system_logger.error(f"PiAdmin daemon bounding error: {e}")
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
                system_logger.debug("Admin daemon no connection")
                continue

            system_logger.success(f"Admin daemon accepted connection from {address}")
            try:
                command = self.__admin_queue.get(block=False)
            except queue.Empty:
                continue

            data = struct.pack("!I", command.value)
            try:
                connection.send(data)
            except socket.error as e:
                system_logger.error(f"Admin daemon failed with error: {e}")
