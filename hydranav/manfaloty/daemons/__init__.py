import multiprocessing
import socket
import time
from core import system_logger, config_manager
from manfaloty.daemons.receiver_daemon import ManfalotyReceiverDaemon
from manfaloty.daemons.sender_daemon import ManfalotySenderDaemon

__all__ = ["ManfalotyDaemonManager"]

RETRY_DELAY = 2
SOCKET_TIMEOUT = 1.0
BASE_IP = config_manager.get("networking", "baseIP")
PI_IP = config_manager.get("networking", "raspIP")
PORT = config_manager.get("manfaloty", "port")


class ManfalotyDaemonManager(multiprocessing.Process):
    def __init__(
        self,
        command_queue: multiprocessing.Queue,
        data_queue: multiprocessing.Queue,
    ):
        super().__init__(daemon=True)
        self.__address = BASE_IP, PORT
        self.__server_socket = self.__create_socket()

        self.__command_queue = command_queue
        self.__data_queue = data_queue
        self.__quit_event = multiprocessing.Event()

        self.__receiver_daemon = ManfalotyReceiverDaemon(
            self.__server_socket,
            self.__data_queue,
            self.__quit_event,
        )
        self.__sender_daemon = ManfalotySenderDaemon(
            self.__server_socket,
            self.__command_queue,
            PI_IP,
            PORT,
            self.__quit_event,
        )

    def start(self):
        self.__receiver_daemon.start()
        self.__sender_daemon.start()
        return super().start()

    def status_ok(self):
        return self.__receiver_daemon.is_alive() and self.__sender_daemon.is_alive()

    def quit(self):
        self.__quit_event.set()
        self.join()
        self.__server_socket.close()

    def join(self, timeout=None):
        self.__receiver_daemon.join()
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
