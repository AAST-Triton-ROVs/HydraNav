from queue import Queue
import socket
import struct
from threading import Thread
import time
from logger import Logging
from rov.enums import GripperCommands


class GripperDaemon(Thread):
    def __init__(
        self,
        gripper_queue: Queue[GripperCommands],
        logging: Logging,
        ip: str,
        port: int,
    ):
        super().__init__(daemon=True)
        self.__gripper_queue = gripper_queue
        self.__logging = logging
        self.__ip = ip
        self.__port = port

        self.gripper_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            self.gripper_socket.bind(self.ip, self.port)
            while True:
                try:
                    self.gripper_socket.connect((self.__ip, self.__port))
                    self.__logging
                    break
                except socket.error:
                    self.__logging.logger.error(
                        f"Failed to connect to {self.__ip}:{self.__port}"
                    )
                    time.sleep(1)

            if not self.__gripper_queue.empty():
                command = self.gripper_queue.get()
                data = struct.pack("i", command.value)
                self.gripper_socket.sendall(data)
