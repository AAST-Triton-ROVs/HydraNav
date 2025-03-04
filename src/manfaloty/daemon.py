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
        self.__address = base_ip, port

        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __bind_socket(self):
        """
        Bind the server socket to the specified address.

        This method attempts to create and bind a UDP socket to the address
        specified by `self.__address`. If the binding is successful, the socket
        is set with a timeout defined by `SERVER_SOCKET_TIMEOUT`, and a success
        message is logged. If an error occurs during the binding process, an
        error message is logged, and the method retries after a delay defined
        by `RECONNECT_DELAY`.

        :raises socket.error: If there is an error creating or binding the socket.
        """
        while True:
            try:
                self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.__server_socket.bind(self.__address)
                self.__server_socket.settimeout(SERVER_SOCKET_TIMEOUT)
                logging.logger.success(
                    f"Manfaloty daemon bound to {self.__address[0]}:{self.__address[1]}"
                )
                return
            except socket.error as e:
                logging.logger.error(f"Manfaloty daemon bounding error: {e}, retrying")
                time.sleep(RECONNECT_DELAY)

    def close_connection(self):
        """
        Closes the server socket connection if it is open.

        This method checks if the server socket is currently open and, if so,
        closes the connection to free up resources.
        """
        if self.__server_socket:
            self.__server_socket.close()

    def run(self):
        """
        Run the daemon to receive and process pH value data.

        This method binds the server socket and enters an infinite loop to 
        continuously receive pH value data from a client. It unpacks the 
        received data, logs the pH value and client information, and puts 
        the pH value into a data queue. If there are any commands in the 
        command queue, it sends the command to the specified Raspberry Pi 
        address.

        Exceptions:
            - socket.timeout: If the socket times out while waiting for data.
            - struct.error: If there is an error unpacking the received data.
            - socket.error: If there is an error sending data through the socket.

        Logging:
            - Logs an error message if there is an error unpacking the data.
            - Logs an error message if there is a socket error while sending data.
            - Logs the received pH value and client information.

        Note:
            - The method will rebind the socket if a socket error occurs while 
              sending data.
        """
        self.__bind_socket()
        while True:
            try:
                data, client = self.__server_socket.recvfrom(PH_VALUE_SIZE)
                ph_value = struct.unpack("f", data)
            except socket.timeout:
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
                self.__server_socket.sendto(data, self.__pi_address)
            except socket.error as e:
                logging.logger.error(f"Manfaloty daemon socket error: {e}")
                self.close_connection()
                self.__bind_socket()
                continue
