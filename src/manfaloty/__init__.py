from queue import Queue
from typing import Tuple

from events import EventDispatcher
from manfaloty.daemon import ManfalotyDaemon
from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands


class Manfaloty:
    class Gripper:
        def __init__(self, client: "Manfaloty"):
            self.client = client

        def open_jaws(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_JAW_OPEN)

        def close_jaws(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_JAW_CLOSE)

        def pitch_up(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_PITCH_UP)

        def pitch_down(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_PITCH_DOWN)

        def roll_left(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_ROLL_LEFT)

        def roll_right(self):
            self.client.__send_command(ManfalotyCommands.GRIPPER_ROLL_RIGHT)

    class Camera:
        def __init__(self, client: "Manfaloty"):
            self.client = client

        def pitch_up(self):
            self.client.__send_command(ManfalotyCommands.CAMERA_PITCH_UP)

        def pitch_down(self):
            self.client.__send_command(ManfalotyCommands.CAMERA_PITCH_DOWN)

    class PHTask:
        def __init__(self, client: "Manfaloty"):
            self.client = client

        def read_ph(self):
            self.client.__send_command(ManfalotyCommands.PH_SENSOR_READ)

        def start_pump(self):
            self.client.__send_command(ManfalotyCommands.PUMP_ON)

        def stop_pump(self):
            self.client.__send_command(ManfalotyCommands.PUMP_OFF)

    def __init__(
        self,
        dispatcher: EventDispatcher,
        pi_ip: str = "192.168.1.100",
        port: int = 2005,
    ):
        self.__command_queue: Queue[ManfalotyCommands] = Queue(1)
        self.__data_queue: Queue[ManfalotyData] = Queue(1)
        self.__dispatcher = dispatcher

        self.__daemon = ManfalotyDaemon(self.__command_queue, self.__data_queue, pi_ip, port)
        self.__daemon.start()

        self.gripper = self.Gripper(self)
        self.camera = self.Camera(self)
        self.ph_task = self.PHTask(self)

    def __send_command(self, command: ManfalotyCommands):
        self.__command_queue.put(command)

    def restart_arduino(self):
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        self.__send_command(ManfalotyCommands.RESET_MOTORS)
        
    def update(self):
        if not self.__data_queue.empty():
            data = self.__data_queue.get()
            if isinstance(data, PHReading):
                self.__dispatcher.dispatch("manfaloty_ph_reading", data.value)
