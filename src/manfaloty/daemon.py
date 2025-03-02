from queue import Queue
import socket
import struct
from threading import Thread
from logger import logging
import time

from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands

RECONNECT_DELAY = 2
SERVER_SOCKET_TIMEOUT = 0.5
PH_VALUE_SIZE = struct.calcsize("f")


class ManfalotyDaemon(Thread):
    def __init__(
        self,
        command_queue: Queue[ManfalotyCommands],
        data_queue: Queue[ManfalotyData],
        base_ip: str,
        pi_ip: str,
        port: int,
    ):
        super().__init__(daemon=True)
        self.__command_queue = command_queue
        self.__data_queue = data_queue
        
        self.__pi_address = pi_ip, port
        self.__address = "0.0.0.0", port

        self.server_socket = self.__bind_socket()

    def __bind_socket(self):
        if not self.server_socket.close():
            return
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.server_socket.bind(self.__address)
                self.server_socket.settimeout(SERVER_SOCKET_TIMEOUT)
                logging.logger.success(
                    f"Manfaloty daemon bound to {self.__address[0]}:{self.__address[1]}"
                )
                return
            except socket.error as e:
                logging.logger.error(f"Manfaloty daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()

    def run(self):
        self.__bind_socket()
        while True:
            try:
                data, client = self.server_socket.recvfrom(PH_VALUE_SIZE)
                ph_value = struct.unpack("f", data)
            except socket.error as e:
                logging.logger.error(f"Manfaloty daemon recvfrom error: {e}")
                self.close_connection()
                self.__bind_socket()
                continue
            except struct.error as e:
                logging.logger.error(f"Manfaloty daemon unpack error: {e}")
                continue
            else:
                logging.logger.info(f"Recieved {ph_value} from {client[0]}:{client[1]}")
                self.__data_queue.put(PHReading(ph_value[0]))


            if self.__command_queue.empty():
                continue

            command = self.__command_queue.get()
            data = struct.pack("i", command.value)
            try:
                self.server_socket.sendto(data, self.__pi_address)
            except socket.error as e:
                logging.logger.error(f"Manfaloty daemon socket error: {e}")
                self.close_connection()
                self.__bind_socket()
                continue
