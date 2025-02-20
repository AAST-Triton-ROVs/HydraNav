from typing import Tuple
from logger import logging
from threading import Thread
from queue import Queue
import socket
import time
import struct


class PiAdminDaemon(Thread):
    def __init__(self, admin_queue: Queue[int], address: Tuple[str, int]):
        super().__init__(daemon=True)
        self.__admin_queue = admin_queue

        self.__address = address
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.__address)

    def run(self):
        self.server_socket.listen()
        while True:
            connection, address = self.server_socket.accept()
            logging.logger.info(f"Admin daemon accepted connection from {address}")
            if not self.__admin_queue.empty():
                command = self.__admin_queue.get()
                data = struct.pack("i", command)
                try:
                    connection.send(data)
                except socket.error as e:
                    logging.logger.error(f"Admin daemon failed with error: {e}")
