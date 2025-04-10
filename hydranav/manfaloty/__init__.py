from queue import Queue
import queue
from core.updatable_mixin import Updatable
from manfaloty.daemons import ManfalotyDaemonManager
from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands
from core import request_manager, event_dispatcher, GCSModule


class Manfaloty(GCSModule, Updatable):
    """
    Manages communication with the Manfaloty system.
    """

    def __init__(self):
        super().__init__()

        self.__command_queue: Queue[ManfalotyCommands] = Queue(1)
        self.__data_queue: Queue[ManfalotyData] = Queue(1)

        self.__daemon_manager = ManfalotyDaemonManager(
            self.__command_queue,
            self.__data_queue,
        )
        self.__daemon_manager.start_daemons()

        event_dispatcher.subscribe(
            "mapper/GRIPPER_JAW_OPEN", lambda _: self.gripper_open_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_JAW_CLOSE", lambda _: self.gripper_close_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/hold/GRIPPER_JAW_OPEN", lambda _: self.gripper_open_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/hold/GRIPPER_JAW_CLOSE", lambda _: self.gripper_close_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_ROLL_LEFT", lambda _: self.gripper_roll_left()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_ROLL_RIGHT", lambda _: self.gripper_roll_right()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_PITCH_UP", lambda _: self.gripper_pitch_up()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_PITCH_DOWN", lambda _: self.gripper_pitch_down()
        )
        request_manager.register_handler(
            "manfaloty/read-ph", lambda _: self.read_ph_sensor()
        )
        request_manager.register_handler("manfaloty/restart", self.restart_arduino)
        request_manager.register_handler("manfaloty/reset", self.reset_motors)
        request_manager.register_handler("manfaloty/start-pump", self.start_pump)
        request_manager.register_handler("manfaloty/stop-pump", self.stop_pump)

    def __send_command(self, command: ManfalotyCommands):
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            return

    def quit(self):
        self.__daemon_manager.quit()

    def status_ok(self) -> bool:
        return self.__daemon_manager.status_ok()

    def restart_arduino(self):
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        self.__send_command(ManfalotyCommands.RESET_MOTORS)

    def gripper_open_jaws(self):
        self.__send_command(ManfalotyCommands.GRIPPER_TOGGLE_JAW_OPEN)

    def gripper_close_jaws(self):
        self.__send_command(ManfalotyCommands.GRIPPER_TOGGLE_JAW_CLOSE)

    def gripper_pitch_up(self):
        self.__send_command(ManfalotyCommands.GRIPPER_PITCH_UP)

    def gripper_pitch_down(self):
        self.__send_command(ManfalotyCommands.GRIPPER_PITCH_DOWN)

    def gripper_roll_left(self):
        self.__send_command(ManfalotyCommands.GRIPPER_ROLL_LEFT)

    def gripper_roll_right(self):
        self.__send_command(ManfalotyCommands.GRIPPER_ROLL_RIGHT)

    def camera_pitch_up(self):
        self.__send_command(ManfalotyCommands.CAMERA_PITCH_UP)

    def camera_pitch_down(self):
        self.__send_command(ManfalotyCommands.CAMERA_PITCH_DOWN)

    def read_ph_sensor(self):
        self.__send_command(ManfalotyCommands.PH_SENSOR_READ)

    def start_pump(self):
        self.__send_command(ManfalotyCommands.PUMP_ON)

    def stop_pump(self):
        self.__send_command(ManfalotyCommands.PUMP_OFF)

    def update(self):
        try:
            data = self.__data_queue.get(block=False)
        except queue.Empty:
            return

        if isinstance(data, PHReading):
            event_dispatcher.dispatch("manfaloty_ph_reading", data.value)
