from logging import Logger
from threading import Thread
from queue import Queue
import socket
import time
import struct

class AdminDaemon(Thread):
    def __init__(self,admin_queue : Queue[int], logging : Logger , ip : str, port : int):
        super().__init__(daemon=True)
        self.__admin_queue = admin_queue
        self.__logging = logging
        self.__ip = ip
        self.__port = port
        self.admin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    def run(self):
        while True:
            self.admin_socket.bind((self.__ip, self.__port))
            while True:
                try:
                    self.admin_socket.connect(("192.168.1.100", self.__port))
                    self.__logging.logger.info(f"Connected to {self.__ip}:{self.__port}")
                    break
                except socket.error:
                    self.__logging.logger.error(f"Failed to connect to {self.__ip}:{self.__port}")
                    time.sleep(1)

            if not self.__admin_queue.empty():
                command = self.__admin_queue.get()
                data = struct.pack("i", command)
                self.admin_socket.sendall(data)