from queue import Queue
import socket
import struct
from threading import Thread
from autopilot.enums import GripperCommands
from logger import logging
import time

RECONNECT_DELAY = 2


class GripperDaemon(Thread):
    def __init__(
        self, gripper_queue: Queue[GripperCommands], base_ip: str, pi_ip: str, port: int
    ):
        super().__init__(daemon=True)
        self.__command_queue = gripper_queue
        self.__pi_address = pi_ip, port
        self.__address = base_ip, port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __bind_socket(self):
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.server_socket.bind(self.__address)
                logging.logger.success(
                    f"Gripper daemon bound to {self.__address[0]}:{self.__address[1]}"
                )
                return
            except socket.error as e:
                logging.logger.error(f"Gripper daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()

    def run(self):
        self.__bind_socket()
        while True:
            if not self.__command_queue.empty():
                command = self.__command_queue.get()
                data = struct.pack("i", command.value)
                try:
                    self.server_socket.sendto(data, self.__pi_address)
                except socket.error as e:
                    logging.logger.error(f"Gripper daemon socket error: {e}")
                    self.close_connection()
                    self.__bind_socket()
                    continue
