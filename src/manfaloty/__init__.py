from queue import Queue
from events import EventDispatcher
from manfaloty.daemon import ManfalotyDaemon
from manfaloty.data import ManfalotyData, PHReading
from manfaloty.enums import ManfalotyCommands


class Manfaloty:
    """
    Manages communication with the Manfaloty system.

    :param dispatcher: Event dispatcher instance
    :type dispatcher: EventDispatcher
    :param base_ip: Base IP address to use
    :type base_ip: str
    :param pi_ip: IP address of the Raspberry Pi
    :type pi_ip: str
    :param port: Port used for communication
    :type port: int
    """

    class Gripper:
        """
        Handles gripper commands for Manfaloty.
        """

        def __init__(self, client: "Manfaloty"):
            """
            Initializes the Gripper.

            :param client: Reference to the main Manfaloty instance
            :type client: Manfaloty
            """
            self.client = client

        def open_jaws(self):
            """
            Opens the jaws of the gripper.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_JAW_OPEN)

        def close_jaws(self):
            """
            Closes the jaws of the gripper.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_JAW_CLOSE)

        def pitch_up(self):
            """
            Pitches the gripper up.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_PITCH_UP)

        def pitch_down(self):
            """
            Pitches the gripper down.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_PITCH_DOWN)

        def roll_left(self):
            """
            Rolls the gripper left.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_ROLL_LEFT)

        def roll_right(self):
            """
            Rolls the gripper right.
            """
            self.client.__send_command(ManfalotyCommands.GRIPPER_ROLL_RIGHT)

    class Camera:
        """
        Handles camera commands.
        """

        def __init__(self, client: "Manfaloty"):
            """
            Initializes the Camera.

            :param client: Reference to the main Manfaloty instance
            :type client: Manfaloty
            """
            self.client = client

        def pitch_up(self):
            """
            Pitches the camera up.
            """
            self.client.__send_command(ManfalotyCommands.CAMERA_PITCH_UP)

        def pitch_down(self):
            """
            Pitches the camera down.
            """
            self.client.__send_command(ManfalotyCommands.CAMERA_PITCH_DOWN)

    class PHTask:
        """
        Handles pH sensor and pump operations.
        """

        def __init__(self, client: "Manfaloty"):
            """
            Initializes the pH task handler.

            :param client: Reference to the main Manfaloty instance
            :type client: Manfaloty
            """
            self.client = client

        def read_ph(self):
            """
            Reads the pH using the sensor.
            """
            self.client.__send_command(ManfalotyCommands.PH_SENSOR_READ)

        def start_pump(self):
            """
            Starts the pump.
            """
            self.client.__send_command(ManfalotyCommands.PUMP_ON)

        def stop_pump(self):
            """
            Stops the pump.
            """
            self.client.__send_command(ManfalotyCommands.PUMP_OFF)

    def __init__(
        self,
        dispatcher: EventDispatcher,
        base_ip: str = "0.0.0.0",
        pi_ip: str = "192.168.1.100",
        port: int = 2005,
    ):
        """
        Creates a Manfaloty instance.

        :param dispatcher: Event dispatcher for handling events
        :type dispatcher: EventDispatcher
        :param base_ip: Local IP address
        :type base_ip: str
        :param pi_ip: Raspberry Pi IP address
        :type pi_ip: str
        :param port: Communication port
        :type port: int
        """
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

        :param command: The command to send
        :type command: ManfalotyCommands
        """
        self.__command_queue.put(command)

    def restart_arduino(self):
        """
        Restarts the Arduino.

        Sends the RESTART_ARDUINO command to the queue.
        """
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        """
        Resets the motors.

        Sends the RESET_MOTORS command to revert motors to default state.
        """
        self.__send_command(ManfalotyCommands.RESET_MOTORS)

    def update(self):
        """
        Updates the internal data by processing queued messages.

        Retrieves data from the queue, checks if it's a PHReading,
        and dispatches 'manfaloty_ph_reading' if applicable.
        """
        if not self.__data_queue.empty():
            data = self.__data_queue.get()
            if isinstance(data, PHReading):
                self.__dispatcher.dispatch("manfaloty_ph_reading", data.value)
