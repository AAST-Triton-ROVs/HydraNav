from queue import Queue
import queue
from event_dispatcher import EventDispatcher
from manfaloty.daemon import ManfalotyDaemon
from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands
from request_manager import RequestManager


class Manfaloty:
    """
    Manages communication with the Manfaloty system.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        request_manager: RequestManager,
        base_ip: str = "0.0.0.0",
        pi_ip: str = "192.168.1.100",
        port: int = 2005,
    ):
        self.__command_queue: Queue[ManfalotyCommands] = Queue(1)
        self.__data_queue: Queue[ManfalotyData] = Queue(1)
        self.__dispatcher = dispatcher
        self.__request_manager = request_manager

        self.__daemon = ManfalotyDaemon(
            self.__command_queue, self.__data_queue, base_ip, pi_ip, port
        )
        self.__daemon.start()

        self.__dispatcher.subscribe(
            "controller_button_down", self.__on_controller_button_down
        )
        self.__dispatcher.subscribe(
            "controller_button_up", self.__on_controller_button_up
        )
        self.__request_manager.register_handler("manfaloty_get_ph", self.read_ph_sensor())

    def __on_controller_button_down(self, button: str):
        match button:
            case "R1":
                self.gripper_toggle_open_jaws()
            case "L1":
                self.gripper_toggle_close_jaws()
            case "R2":
                self.gripper_roll_right()
            case "L2":
                self.gripper_roll_left()
            case "R4":
                self.gripper_pitch_up()
            case "L4":
                self.gripper_pitch_down()

    def __on_controller_button_up(self, button: str):
        match button:
            case "R1":
                self.gripper_toggle_open_jaws()
            case "L1":
                self.gripper_toggle_close_jaws()

    def __send_command(self, command: ManfalotyCommands):
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            self.__command_queue.get()
            self.__send_command(command)

    def restart_arduino(self):
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        self.__send_command(ManfalotyCommands.RESET_MOTORS)

    def gripper_toggle_open_jaws(self):
        self.__send_command(ManfalotyCommands.GRIPPER_TOGGLE_JAW_OPEN)

    def gripper_toggle_close_jaws(self):
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
        if not self.__data_queue.empty():
            data = self.__data_queue.get()
            if isinstance(data, PHReading):
                self.__dispatcher.dispatch("manfaloty_ph_reading", data.value)
