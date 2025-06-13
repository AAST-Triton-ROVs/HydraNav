import multiprocessing
import queue
import socket
import struct
import time

import cv2
import numpy as np
from hydranav.core import LoggerMixin, config_manager

TARGET_WIDTH = config_manager["cameraStreamer", "targetWidth"]
TARGET_HEIGHT = config_manager["cameraStreamer", "targetHeight"]
RASP_IP = config_manager["networking", "raspIP"]
FPS = config_manager["cameraStreamer", "FPS"]

I_SIZE = struct.calcsize("!I")
TIMEOUT = 1 / FPS


class CameraDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(
        self,
        port: int,
        data_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        multiprocessing.Process.__init__(self, daemon=True)
        LoggerMixin.__init__(self)
        self.__data_queue = data_queue
        self.__quit_event = quit_event
        self.__port = port

    def run(self):
        while not self.__quit_event.is_set():
            self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.__client_socket.connect((RASP_IP, self.__port))
            except (OSError, ConnectionRefusedError):
                self.__client_socket.close()
                time.sleep(1)
                continue

            self._logger.info(f"Connected to ({RASP_IP}, {self.__port})")
            connection_closed = False

            data = b""
            while not self.__quit_event.is_set():
                while len(data) < I_SIZE:
                    try:
                        packet = self.__client_socket.recv(4096)
                    except ConnectionResetError:
                        connection_closed = True
                        break
                    if not packet:
                        self._logger.debug("Connection Closed")
                        connection_closed = True
                        break
                    data += packet
                if connection_closed:
                    break
                packed_msg_size = data[:I_SIZE]
                data = data[I_SIZE:]
                msg_size = struct.unpack("!I", packed_msg_size)[0]

                while len(data) < msg_size:
                    try:
                        packet = self.__client_socket.recv(4096)
                    except ConnectionResetError:
                        connection_closed = True
                        break
                    if not packet:
                        self._logger.debug("Connection Closed")
                        connection_closed = True
                        break
                    data += packet
                if connection_closed:
                    break
                msg_data = data[:msg_size]
                data = data[msg_size:]

                nparr = np.frombuffer(msg_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
                try:
                    self.__data_queue.put(frame, block=False)
                except queue.Full:
                    continue
