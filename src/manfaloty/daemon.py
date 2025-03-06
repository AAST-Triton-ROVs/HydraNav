from queue import Queue
import socket
import struct
from threading import Thread
from logger import system_logger
import time

from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands

RECONNECT_DELAY = 2
SERVER_SOCKET_TIMEOUT = 0.5
PH_VALUE_SIZE = struct.calcsize("f")


class ManfalotyDaemon(Thread):
    """
    Runs a daemon handling pH data and commands.

    :param command_queue: Commands to send
    :type command_queue: Queue[ManfalotyCommands]
    :param data_queue: Stores incoming data
    :type data_queue: Queue[ManfalotyData]
    :param base_ip: Local IP address
    :type base_ip: str
    :param pi_ip: Remote Pi IP address
    :type pi_ip: str
    :param port: Communication port
    :type port: int
    """

    def __init__(
        self,
        command_queue: Queue[ManfalotyCommands],
        data_queue: Queue[ManfalotyData],
        base_ip: str,
        pi_ip: str,
        port: int,
    ):
        """
        Initializes the daemon.
        """
        super().__init__(daemon=True)
        self.__command_queue = command_queue
        self.__data_queue = data_queue
        self.__pi_address = pi_ip, port
        self.__address = base_ip, port
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __bind_socket(self):
        """
        Binds the socket to the address.

        :raises socket.error: On socket failure
        """
        while True:
            try:
                self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.__server_socket.bind(self.__address)
                self.__server_socket.settimeout(SERVER_SOCKET_TIMEOUT)
                system_logger.success(
                    f"Manfaloty daemon bound to {self.__address[0]}:{self.__address[1]}"
                )
                return
            except socket.error as e:
                system_logger.error(f"Manfaloty daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        """
        Closes the socket to free resources.
        """
        if self.__server_socket:
            self.__server_socket.close()

    def run(self):
        """
        Runs the daemon loop to receive and send data.

        :raises socket.timeout: If no data is received in time
        :raises struct.error: If data unpack fails
        :raises socket.error: If sending via socket fails
        """
        self.__bind_socket()
        while True:
            try:
                data, client = self.__server_socket.recvfrom(PH_VALUE_SIZE)
                ph_value = struct.unpack("f", data)
            except socket.timeout:
                continue
            except struct.error as e:
                system_logger.error(f"Manfaloty daemon unpack error: {e}")
                continue
            else:
                system_logger.info(f"Recieved {ph_value} from {client[0]}:{client[1]}")
                self.__data_queue.put(PHReading(ph_value[0]))

            if self.__command_queue.empty():
                continue

            command = self.__command_queue.get()
            data = struct.pack("i", command.value)
            try:
                self.__server_socket.sendto(data, self.__pi_address)
            except socket.error as e:
                system_logger.error(f"Manfaloty daemon socket error: {e}")
                self.close_connection()
                self.__bind_socket()
