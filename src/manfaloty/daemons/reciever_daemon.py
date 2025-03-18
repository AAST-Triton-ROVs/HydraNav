from queue import Queue
import socket
import struct
from threading import Thread
import threading
from core.logger import system_logger
import time

from manfaloty.data import ManfalotyData, PHReading

PH_VALUE_SIZE = struct.calcsize("!f")


class ManfalotyRecieverDaemon(Thread):
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
        data_queue: Queue[ManfalotyData],
        quit_event: threading.Event,
    ):
        super().__init__(daemon=True)
        self.__data_queue = data_queue
        self.__server_socket = server_socket
        self.__quit_event = quit_event
        
    def run(self):
        while not self.__quit_event.is_set():
            try:
                data, client = self.__server_socket.recvfrom(PH_VALUE_SIZE)
                ph_value = struct.unpack("!f", data)
            except socket.timeout:
                system_logger.debug("Manfaloty reciever reading from socket timeout")
                continue
            except socket.error as e:
                system_logger.error(f"Manfaloty reciever daemon socket error: {e}")
                continue
            except struct.error as e:
                system_logger.error(f"Manfaloty reciever daemon unpack error: {e}")
                continue

            system_logger.success(f"Recieved data from {client[0]}:{client[1]}")
            self.__data_queue.put(PHReading(ph_value[0]))