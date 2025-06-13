import multiprocessing
import multiprocessing.synchronize
import queue
import socket
import struct
import time

import cv2
from fastapi import Response
import numpy as np
from hydranav.core import (
    GCSModule,
    config_manager,
    Updatable,
    stream_dispatcher,
)
from hydranav.core.has_webgui import HasWebGUI
from hydranav.vision.streaming.camera_daemon import CameraDaemon
from nicegui import app, ui, run


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
_, CAMERA_OFFLINE_JPEG = cv2.imencode(".jpg", CAMERA_OFFLINE_FRAME)
I_SIZE = struct.calcsize("!I")
FRAME_RETRIEVAL_TIMEOUT = 0.03


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

        self.__ui_frame_1_pipe = stream_dispatcher.request_stream("camera-streamer/1")
        self.__ui_frame_2_pipe = stream_dispatcher.request_stream("camera-streamer/2")
        self.__ui_frame_3_pipe = stream_dispatcher.request_stream("camera-streamer/3")
        self.__ui_frame_4_pipe = stream_dispatcher.request_stream("camera-streamer/4")

        for i in range(1, MAX_CAMERA_COUNT + 1):
            port = BASE_PORT + i
            data_queue: multiprocessing.Queue[np.ndarray] = multiprocessing.Queue(1)
            daemon = CameraDaemon(port, data_queue, self.__quit_event)
            daemon.start()

            self.__data_queues[port] = data_queue
            self.__daemons[port] = daemon

    def webgui_contents(self):
        container = ui.grid(columns=2, rows=2).classes("w-full")
        with container:
            frame_1 = ui.interactive_image(size=(TARGET_WIDTH, TARGET_HEIGHT)).classes(
                "w-1/2"
            )
            frame_2 = ui.interactive_image(size=(TARGET_WIDTH, TARGET_HEIGHT)).classes(
                "w-1/2"
            )
            frame_3 = ui.interactive_image(size=(TARGET_WIDTH, TARGET_HEIGHT)).classes(
                "w-1/2"
            )
            frame_4 = ui.interactive_image(size=(TARGET_WIDTH, TARGET_HEIGHT)).classes(
                "w-1/2"
            )

        @app.get("/camera-streamer/video/{camera_index}")
        async def grab_video_frame(camera_index: int) -> Response:
            match camera_index:
                case 1:
                    pipe = self.__ui_frame_1_pipe
                case 2:
                    pipe = self.__ui_frame_2_pipe
                case 3:
                    pipe = self.__ui_frame_3_pipe
                case 4:
                    pipe = self.__ui_frame_4_pipe
                case _:
                    return Response(content="Invalid camera index", status_code=400)

            if pipe.poll(timeout=0.5):
                frame = pipe.recv()
                jpeg = await run.cpu_bound(_convert, frame)
            else:
                jpeg = CAMERA_OFFLINE_JPEG.tobytes()

            return Response(content=jpeg, media_type="image/jpeg")

        def update_frames():
            frame_1.set_source(f"/camera-streamer/video/1?{time.time()}")
            frame_2.set_source(f"/camera-streamer/video/2?{time.time()}")
            frame_3.set_source(f"/camera-streamer/video/3?{time.time()}")
            frame_4.set_source(f"/camera-streamer/video/4?{time.time()}")

        ui.timer(
            interval=0.029,
            callback=update_frames,
        )

        return container

    def webgui_icon_name(self):
        return "videocam"

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
        frames: dict[int, np.ndarray] = {}
        for port, data_queue in self.__data_queues.items():
            try:
                frame = data_queue.get(timeout=FRAME_RETRIEVAL_TIMEOUT)
                frames[port] = frame
            except queue.Empty:
                continue

        # for port, frame in frames.items():
        #     stream_dispatcher.dispatch(f"camera-streamer/{port - BASE_PORT}", frame)

        for i in range(1, MAX_CAMERA_COUNT + 1):
            if frames.get(BASE_PORT + i) is None:
                frames[BASE_PORT + i] = CAMERA_OFFLINE_FRAME

        columns = 2
        rows = (len(frames) + columns - 1) // columns

        grid_image = np.zeros(
            (
                rows * TARGET_HEIGHT,
                columns * TARGET_WIDTH,
                frames[2031].shape[2],
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

        cv2.imshow("grid", grid_image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.quit()
