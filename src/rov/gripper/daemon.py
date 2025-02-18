from queue import Queue
import socket
import struct
from threading import Thread
import time
from typing import Tuple
from logger import logging
from rov.enums import GripperCommands


class GripperDaemon(Thread):
    def __init__(
        self, gripper_queue: Queue[GripperCommands], base_ip: str, pi_ip: str, port: int
    ):
        super().__init__(daemon=True)
        self.__command_queue = gripper_queue
        self.__address = (base_ip, port)
        self.__pi_address = pi_ip, port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            self.server_socket.bind(self.__address)
            while True:
                try:
                    self.server_socket.connect(self.__address)
                    break
                except socket.error:
                    logging.logger.error(
                        f"Failed to connect to {self.__address[0]}:{self.__address[1]}"
                    )
                    time.sleep(1)

            if not self.__command_queue.empty():
                command = self.__command_queue.get()
                data = struct.pack("i", command.value)
                self.server_socket.sendto(data, self.__pi_address)
