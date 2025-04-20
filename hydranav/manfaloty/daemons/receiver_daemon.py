import multiprocessing
import multiprocessing.synchronize
import queue
import socket
import struct

from core import system_logger
from manfaloty.data import PHReading

PH_VALUE_SIZE = struct.calcsize("!f")


class ManfalotyReceiverDaemon(multiprocessing.Process):
    """
    A daemon thread responsible for receiving sensor data from the Manfaloty.
    This class continuously reads incoming raw pH values from a server socket, unpacks
    the data into a floating-point value, logs the received data, and places it into a
    shared queue for inter-process communication

    :param server_socket: The socket object used to receive data from the Manfaloty device.
    :type server_socket: socket.socket
    :param data_queue: A queue that holds received ManfalotyData instances, where pH readings are placed.
    :type data_queue: Queue[ManfalotyData]
    """

    def __init__(
        self,
        server_socket: socket.socket,
        data_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        super().__init__(daemon=True)
        self.__data_queue = data_queue
        self.__server_socket = server_socket
        self.__quit_event = quit_event

    def run(self):
        while not self.__quit_event.is_set():
            try:
                data, client = self.__server_socket.recvfrom(PH_VALUE_SIZE)
            except socket.timeout:
                system_logger.debug("Manfaloty receiver reading from socket timeout")
                continue
            except socket.error as e:
                system_logger.error(f"Manfaloty receiver daemon socket error: {e}")
                continue
            
            try:
                ph_value = struct.unpack("!f", data)
            except struct.error as e:
                system_logger.error(f"Manfaloty receiver daemon unpack error: {e}")
                continue

            system_logger.success(f"Recieved data from {client[0]}:{client[1]}")
            try:
                self.__data_queue.put(PHReading(ph_value[0]), block=False)
            except queue.Full:
                system_logger.error("Unable to put ph reading into data queue")
                return
