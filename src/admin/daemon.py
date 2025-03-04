from typing import Tuple
from admin.enums import AdminCommands
from logger import logging
from threading import Thread
from queue import Queue
import socket
import time
import struct


class PiAdminDaemon(Thread):
    def __init__(self, admin_queue: Queue[AdminCommands], address: Tuple[str, int]):
        super().__init__(daemon=True)
        self.__admin_queue = admin_queue

        self.__address = address
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.__address)

    def run(self):
        """
        Run the admin daemon to listen for incoming connections and process commands.

        This method starts the server socket listening for incoming connections. When a connection
        is accepted, it logs the connection address. If there are commands in the admin queue, it
        retrieves the command, packs it into a binary format, and sends it to the connected client.
        If an error occurs while sending data, it logs the error.

        :raises socket.error: If there is an error sending data to the client.
        """
        self.server_socket.listen()
        while True:
            connection, address = self.server_socket.accept()
            logging.logger.info(f"Admin daemon accepted connection from {address}")
            if not self.__admin_queue.empty():
                command = self.__admin_queue.get()
                data = struct.pack("i", command.value)
                try:
                    connection.send(data)
                except socket.error as e:
                    logging.logger.error(f"Admin daemon failed with error: {e}")
