import multiprocessing
import multiprocessing.synchronize
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
CLAHE = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))


class CameraDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(
        self,
        port: int,
        data_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
        use_enhancement: multiprocessing.synchronize.Event,
        rotate180: multiprocessing.synchronize.Event,
    ):
        multiprocessing.Process.__init__(self, daemon=True)
        LoggerMixin.__init__(self)
        self.__data_queue = data_queue
        self.__quit_event = quit_event
        self.__port = port
        self.__use_enhancement = use_enhancement
        self.__rotate180 = rotate180

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

                # # Apply sharpening using unsharp masking
                # gaussian_blur = cv2.GaussianBlur(frame, (0, 0), 3)
                # unsharp_mask = cv2.addWeighted(frame, 1.5, gaussian_blur, -0.5, 0)
                # frame = cv2.addWeighted(frame, 1.5, unsharp_mask, -0.5, 0)

                if self.__use_enhancement.is_set():
                    lab = cv2.cvtColor(
                        frame, cv2.COLOR_BGR2LAB
                    )  # convert from BGR to LAB color space
                    l, a, b = cv2.split(  # noqa: E741
                        lab
                    )  # split on 3 different channels

                    lab = cv2.merge((CLAHE.apply(l), a, b))  # merge channels
                    frame = cv2.cvtColor(
                        lab, cv2.COLOR_LAB2BGR
                    )  # convert from LAB to BGR

                if self.__rotate180.is_set():
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                try:
                    self.__data_queue.put(frame, block=False)
                except queue.Full:
                    try:
                        self.__data_queue.get(block=False)
                    except queue.Empty:
                        continue

                    self.__data_queue.put(frame, block=False)
