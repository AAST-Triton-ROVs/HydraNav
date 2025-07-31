import multiprocessing
import multiprocessing.synchronize
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
from hydranav.core.has_webgui import HasWebGUI
from hydranav.vision.streaming.camera_daemon import CameraDaemon
from nicegui import ui

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
CAMERA_OFFLINE_TIMEOUT = 2.0


def _convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image.

    This is a free function (not in a class or inner-function),
    to allow run.cpu_bound to pickle it and send it to a separate process.
    """
    _, imencode_image = cv2.imencode(".jpg", frame)
    return imencode_image.tobytes()


class CameraStreamer(GCSModule, Updatable, HasWebGUI):
    def __init__(self):
        super().__init__()

        self.__quit_event = multiprocessing.Event()
        self.__daemons: dict[int, multiprocessing.Process] = {}
        self.__data_queues: dict[int, multiprocessing.Queue[np.ndarray]] = {}

        self.__previous_frames: dict[int, np.ndarray] = {
            i: CAMERA_OFFLINE_FRAME for i in range(1, MAX_CAMERA_COUNT + 1)
        }
        self.__last_frame_time: dict[int, float] = {}
        self.__camera_labels: dict[int, ui.label] = {}
        self.__camera_use_enhancement: dict[int, multiprocessing.synchronize.Event] = {}
        self.__camera_rotate180: dict[int, multiprocessing.synchronize.Event] = {}

        cv2.namedWindow("HydraNav Cameras", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "HydraNav Cameras",
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN,
        )

        for i in range(1, MAX_CAMERA_COUNT + 1):
            port = BASE_PORT + i
            data_queue: multiprocessing.Queue[np.ndarray] = multiprocessing.Queue(1)
            use_enhancement = multiprocessing.Event()
            rotate180 = multiprocessing.Event()
            daemon = CameraDaemon(
                port,
                data_queue,
                self.__quit_event,
                use_enhancement,
                rotate180,
            )
            daemon.start()

            self.__data_queues[i] = data_queue
            self.__daemons[i] = daemon
            self.__camera_use_enhancement[i] = use_enhancement
            self.__camera_rotate180[i] = rotate180

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
        for i, data_queue in self.__data_queues.items():
            try:
                frame = data_queue.get(block=False)
                frames[i] = frame
            except queue.Empty:
                current_time = time.monotonic()

                if i not in self.__last_frame_time:
                    self.__last_frame_time[i] = current_time

                if current_time - self.__last_frame_time[i] >= CAMERA_OFFLINE_TIMEOUT:
                    frames[i] = CAMERA_OFFLINE_FRAME
            else:
                if i in self.__last_frame_time:
                    del self.__last_frame_time[i]

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

    def webgui_contents(self):
        container = ui.column(align_items="center").classes("w-full")
        with container:
            with ui.card().classes("w-1/2 justify-center items-center"):
                ui.label("Camera Streamer").classes(
                    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
                )
                for i in range(1, MAX_CAMERA_COUNT + 1):
                    with ui.row().classes("w-full justify-center"):
                        self.__camera_labels[i] = ui.label(f"Camera {i}").classes(
                            "w-1/4 text-center"
                        )

                        ui.button(
                            "Enhance",
                            on_click=lambda num=i: self.__webgui_camera_use_enhancement_toggle(
                                num
                            ),
                        ).classes("w-1/3")
                        ui.button(
                            "Rotate 180",
                            on_click=lambda num=i: self.__webgui_camera_rotate180_toggle(
                                num
                            ),
                        ).classes("w-1/3")
        return container

    def webgui_icon_name(self):
        return "videocam"

    def __webgui_camera_rotate180_toggle(self, number: int):
        if number not in self.__camera_rotate180:
            return

        if self.__camera_rotate180[number].is_set():
            self.__camera_rotate180[number].clear()
        else:
            self.__camera_rotate180[number].set()

    def __webgui_camera_use_enhancement_toggle(self, number: int):
        if number not in self.__camera_use_enhancement:
            return

        if self.__camera_use_enhancement[number].is_set():
            self.__camera_use_enhancement[number].clear()
        else:
            self.__camera_use_enhancement[number].set()
