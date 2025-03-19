from queue import Queue
import queue
import socket
import struct
from threading import Thread
import threading
import time

from core.logger import system_logger
from manfaloty.enums import ManfalotyCommands

RETRY_DELAY = 2


class ManfalotySenderDaemon(Thread):
    """
    A daemon thread responsible for sending commands to the Manfaloty system.
    This thread continuously checks if any commands are available in the command queue.
    When a command is found, it is packed and sent to the specified address. Errors
    encountered during socket communication are logged, and automatic reconnection
    attempts are made after a delay if needed.

    :param server_socket: The socket used for transmitting command data.
    :type server_socket: socket.socket
    :param command_queue: A queue holding commands to be sent to the target system.
    :type command_queue: Queue[ManfalotyCommands]
    :param pi_ip: The IP address of the Manfaloty system.
    :type pi_ip: str
    :param port: The port on which the Manfaloty system is listening.
    :type port: int
    """

    def __init__(
        self,
        server_socket: socket.socket,
        command_queue: Queue[ManfalotyCommands],
        pi_ip: str,
        port: int,
        quit_event: threading.Event,
    ):
        super().__init__(daemon=True)
        self.__command_queue = command_queue
        self.__pi_address = pi_ip, port
        self.__server_socket = server_socket
        self.__quit_event = quit_event

    def run(self):
        while not self.__quit_event.is_set():
            try:
                command = self.__command_queue.get(block=False)
            except queue.Empty:
                system_logger.trace("Manfaloty daemon no new commands")
                continue

            system_logger.info(f"Sending {command.value} to {self.__pi_address}")

            try:
                data = struct.pack("!i", command.value)
            except struct.error as e:
                system_logger.critical(f"Manfaloty Sender daemon packing error: {e}")
                continue
            
            try:
                self.__server_socket.sendto(data, self.__pi_address)
            except socket.timeout:
                system_logger.debug("Manfaloty client not connected")
                continue
            except socket.error as e:
                system_logger.error(f"Manfaloty sender daemon socket error: {e}")
                continue

            system_logger.success(
                f"Sent {command.value} to {self.__pi_address[0]}:{self.__pi_address[1]}"
            )
