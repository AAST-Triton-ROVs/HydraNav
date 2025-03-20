from queue import Queue
import socket
import threading
import time
from core import system_logger
from manfaloty.daemons.reciever_daemon import ManfalotyRecieverDaemon
from manfaloty.daemons.sender_daemon import ManfalotySenderDaemon
from manfaloty.data import ManfalotyData
from manfaloty.enums import ManfalotyCommands

__all__ = ["ManfalotyDaemonManager"]

RETRY_DELAY = 2
SOCKET_TIMEOUT = 1.0


class ManfalotyDaemonManager:
    def __init__(
        self,
        command_queue: Queue[ManfalotyCommands],
        data_queue: Queue[ManfalotyData],
        base_ip: str,
        pi_ip: str,
        port: int,
    ):
        self.__address = base_ip, port
        self.__server_socket = self.__create_socket()

        self.__command_queue = command_queue
        self.__data_queue = data_queue
        self.__quit_event = threading.Event()

        self.__reciever_daemon = ManfalotyRecieverDaemon(
            self.__server_socket,
            self.__data_queue,
            self.__quit_event,
        )
        self.__sender_daemon = ManfalotySenderDaemon(
            self.__server_socket,
            self.__command_queue,
            pi_ip,
            port,
            self.__quit_event,
        )

    def start_daemons(self):
        self.__reciever_daemon.start()
        self.__sender_daemon.start()
        
    def status_ok(self):
        return self.__reciever_daemon.is_alive() and self.__sender_daemon.is_alive()

    def quit(self):
        self.__quit_event.set()
        self.join()
        self.__server_socket.close()
        
    def join(self):
        self.__reciever_daemon.join()
        self.__sender_daemon.join()

    def __create_socket(self) -> socket.socket:
        """
        Binds the socket to the address.

        :raises socket.error: On socket failure
        """
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.settimeout(SOCKET_TIMEOUT)
                server_socket.bind(self.__address)
            except socket.error as e:
                system_logger.error(f"Manfaloty daemon bounding error: {e}, retrying")
                time.sleep(RETRY_DELAY)
                continue
        
            system_logger.success(
                f"Manfaloty daemons bound to {self.__address[0]}:{self.__address[1]}"
            )
            return server_socket
