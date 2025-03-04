from queue import Queue
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
        base_ip: str = "0.0.0.0",
        pi_ip: str = "192.168.1.100",
        port: int = 2005,
    ):
        self.__command_queue: Queue[ManfalotyCommands] = Queue(1)
        self.__data_queue: Queue[ManfalotyData] = Queue(1)
        self.__dispatcher = dispatcher

        self.__daemon = ManfalotyDaemon(
            self.__command_queue, self.__data_queue, base_ip, pi_ip, port
        )
        self.__daemon.start()

        self.gripper = self.Gripper(self)
        self.camera = self.Camera(self)
        self.ph_task = self.PHTask(self)

    def __send_command(self, command: ManfalotyCommands):
        """
        Sends a command to the command queue.

        :param command: The command to be sent.
        :type command: ManfalotyCommands
        """
        self.__command_queue.put(command)

    def restart_arduino(self):
        """
        Restart the Arduino by sending the appropriate command.

        This method sends the RESTART_ARDUINO command to the Arduino
        to initiate a restart sequence.

        :return: None
        """
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        """
        Resets the motors by sending the RESET_MOTORS command.

        This method sends a command to reset the motors to their default state.
        It uses the `__send_command` method with the `ManfalotyCommands.RESET_MOTORS` command.

        :return: None
        """
        self.__send_command(ManfalotyCommands.RESET_MOTORS)

    def update(self):
        """
        Update method that processes data from the internal queue.

        This method checks if the internal data queue is not empty. If there is data in the queue,
        it retrieves the data and checks if it is an instance of `PHReading`. If so, it dispatches
        the `manfaloty_ph_reading` event with the pH reading value.

        :raises queue.Empty: If the queue is empty when attempting to retrieve data.
        """
        if not self.__data_queue.empty():
            data = self.__data_queue.get()
            if isinstance(data, PHReading):
                self.__dispatcher.dispatch("manfaloty_ph_reading", data.value)
