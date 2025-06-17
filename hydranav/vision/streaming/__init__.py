import multiprocessing
import queue
import struct
import time
import cv2
import numpy as np
from hydranav.core import (
    GCSModule,
    config_manager,
    Updatable,
    stream_dispatcher,
)
from hydranav.vision.streaming.camera_daemon import CameraDaemon


RASP_IP = config_manager["networking", "raspIP"]
BASE_PORT = config_manager["cameraStreamer", "basePort"]
MAX_CAMERA_COUNT = config_manager["cameraStreamer", "maxCameraCount"]
TARGET_WIDTH = config_manager["cameraStreamer", "targetWidth"]
TARGET_HEIGHT = config_manager["cameraStreamer", "targetHeight"]
CAMERA_OFFLINE_FRAME = cv2.putText(
    np.zeros((TARGET_HEIGHT, TARGET_WIDTH, 3), np.uint8) * 255,
    "Camera Offline",
    (
        (
            TARGET_WIDTH
            - cv2.getTextSize("Camera Offline", cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0][0]
        )
        // 2,
        (
            TARGET_HEIGHT
            + cv2.getTextSize("Camera Offline", cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0][1]
        )
        // 2,
    ),
    cv2.FONT_HERSHEY_SIMPLEX,
    2,
    (255, 255, 255),
    3,
)
I_SIZE = struct.calcsize("!I")
CAMERA_OFFLINE_TIMEOUT = 1.0


def _convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image.

    This is a free function (not in a class or inner-function),
    to allow run.cpu_bound to pickle it and send it to a separate process.
    """
    _, imencode_image = cv2.imencode(".jpg", frame)
    return imencode_image.tobytes()


class CameraStreamer(GCSModule, Updatable):
    def __init__(self):
        super().__init__()

        self.__quit_event = multiprocessing.Event()
        self.__daemons: dict[int, multiprocessing.Process] = {}
        self.__data_queues: dict[int, multiprocessing.Queue[np.ndarray]] = {}

        self.__ui_frame_1_pipe = stream_dispatcher.request_stream("camera-streamer/1")
        self.__ui_frame_2_pipe = stream_dispatcher.request_stream("camera-streamer/2")
        self.__ui_frame_3_pipe = stream_dispatcher.request_stream("camera-streamer/3")
        self.__ui_frame_4_pipe = stream_dispatcher.request_stream("camera-streamer/4")

        self.__previous_frames: dict = {
            2031: CAMERA_OFFLINE_FRAME,
            2032: CAMERA_OFFLINE_FRAME,
            2033: CAMERA_OFFLINE_FRAME,
            2034: CAMERA_OFFLINE_FRAME,
        }
        self.__last_frame_time: dict[int, float] = {}

        for i in range(1, MAX_CAMERA_COUNT + 1):
            port = BASE_PORT + i
            data_queue: multiprocessing.Queue[np.ndarray] = multiprocessing.Queue(1)
            daemon = CameraDaemon(port, data_queue, self.__quit_event)
            daemon.start()

            self.__data_queues[port] = data_queue
            self.__daemons[port] = daemon

    @classmethod
    def init_order(cls):
        return 100

    def status_ok(self):
        return all(daemon.is_alive() for daemon in self.__daemons.values())

    def quit(self):
        self.__quit_event.set()
        for daemon in self.__daemons.values():
            daemon.join(timeout=1)
        cv2.destroyAllWindows()
        return

    def update(self):
        frames: dict[int, np.ndarray] = self.__previous_frames
        for port, data_queue in self.__data_queues.items():
            try:
                frame = data_queue.get(block=False)
                frames[port] = frame
            except queue.Empty:
                current_time = time.monotonic()

                if port not in self.__last_frame_time:
                    self.__last_frame_time[port] = current_time

                if (
                    current_time - self.__last_frame_time[port]
                    >= CAMERA_OFFLINE_TIMEOUT
                ):
                    frames[port] = CAMERA_OFFLINE_FRAME
            else:
                if port in self.__last_frame_time:
                    del self.__last_frame_time[port]

        self.__previous_frames = frames

        columns = 2
        rows = (len(frames) + columns - 1) // columns

        grid_image = np.zeros(
            (
                rows * TARGET_HEIGHT,
                columns * TARGET_WIDTH,
                3,
            ),
            dtype=np.uint8,
        )

        for i, frame in enumerate(frames.values()):
            row = i // columns
            col = i % columns
            grid_image[
                row * TARGET_HEIGHT : (row + 1) * TARGET_HEIGHT,
                col * TARGET_WIDTH : (col + 1) * TARGET_WIDTH,
                :,
            ] = frame

        cv2.imshow("HydraNav Cameras", grid_image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.quit()
