from queue import PriorityQueue, Queue
from typing import Tuple
from events import EventDispatcher
from numpy import interp
from autopilot.daemon import AutopilotConnectionDaemon
from autopilot.movement import ROVMovement
from autopilot.command import ROVCommands
from autopilot.notification import (
    Armed,
    Disarmed,
    GainChange,
    ROVNotification,
    SystemModeChanged,
    VehicleConnected,
    VehicleDisconnected,
)

__exports__ = ["ROV"]


class Autopilot:
    """
    Manages and controls the Pixhawk autopilot.

    Handles communication with the ROV, processes movement commands, sends control
    commands, and dispatches notifications. All commands are placed into thread-safe
    queues, read by :class:`AutopilotConnectionDaemon`.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        base_ip: str = "0.0.0.0",
        port: int = 2000,
    ):
        """
        Initializes Autopilot.

        :param dispatcher: Event dispatcher for broadcasting messages.
        :type dispatcher: EventDispatcher
        :param base_ip: Listen IP, defaults to "0.0.0.0".
        :type base_ip: str
        :param port: Port to bind, defaults to 2000.
        :type port: int
        """
        self.__movement_queue: Queue[ROVMovement] = Queue(1)
        self.__command_queue: Queue[ROVCommands] = Queue(1)
        self.__notification_queue: PriorityQueue[ROVNotification] = PriorityQueue()

        self.__dispatcher = dispatcher

        self.__connection_daemon = AutopilotConnectionDaemon(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            base_ip,
            port,
        )
        self.__connection_daemon.start()

        self.__dispatcher.subscribe(
            "controller_button_down", self.__on_controller_button_down
        )
        self.__dispatcher.subscribe(
            "controller_joysticks", self.__handle_controller_joysticks
        )

    def __handle_controller_joysticks(self, move: Tuple[float, float, float, float]):
        x, y, z, w = move

        self.move(x, y, z, w, 0)

    def __move(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        """
        Queues a movement command.

        :param forward: Forward/backward value.
        :type forward: float
        :param lateral: Lateral movement value.
        :type lateral: float
        :param throttle: Vertical movement value.
        :type throttle: float
        :param yaw: Yaw value.
        :type yaw: float
        :param roll: Roll value.
        :type roll: float
        """
        self.__movement_queue.put(ROVMovement(forward, lateral, throttle, yaw, roll))

    def __on_controller_button_down(self, button: str):
        match button:
            case "A":
                self.arm()
            case "B":
                self.disarm()
            case "C":
                self.flight_mode_stabilize()
            case "D":
                self.flight_mode_manual()
            case "3":
                self.gain_up()
            case "1":
                self.gain_down()
            case "2":
                self.move(0, 0, 0, 0, 1.0)
            case "4":
                self.move(0, 0, 0, 0, -1.0)

    def __command(self, command: ROVCommands):
        """
        Queues a command for the autopilot.

        :param command: ROV command to be sent.
        :type command: ROVCommands
        """
        self.__command_queue.put(command)

    def move(
        self,
        forward: float,
        lateral: float,
        throttle: float,
        yaw: float,
        roll: float,
        min_joy_value: int = -100,
        max_joy_value: int = 100,
    ):
        """
        Interprets joystick inputs and issues movement commands.

        :param forward: Forward/backward joystick input.
        :type forward: float
        :param lateral: Lateral joystick input.
        :type lateral: float
        :param throttle: Throttle joystick input.
        :type throttle: float
        :param yaw: Yaw joystick input.
        :type yaw: float
        :param roll: Roll joystick input.
        :type roll: float
        :param min_joy_value: Minimum joystick value, defaults to -100.
        :type min_joy_value: int
        :param max_joy_value: Maximum joystick value, defaults to 100.
        :type max_joy_value: int
        """
        self.__move(
            interp(forward, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(lateral, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(throttle, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(yaw, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(roll, [min_joy_value, max_joy_value], [-1.0, 1.0]),
        )

    def gain_up(self):
        """
        Sends the gain-up command.
        """
        self.__command(ROVCommands.GAIN_UP)

    def gain_down(self):
        """
        Sends the gain-down command.
        """
        self.__command(ROVCommands.GAIN_DOWN)

    def arm(self):
        """
        Sends the arm command.
        """
        self.__command(ROVCommands.ARM)

    def disarm(self):
        """
        Sends the disarm command.
        """
        self.__command(ROVCommands.DISARM)

    def flight_mode_manual(self):
        """
        Puts the vehicle into manual flight mode.
        """
        self.__command(ROVCommands.SYSTEM_MODE_MANUAL)

    def flight_mode_stabilize(self):
        """
        Puts the vehicle into stabilize flight mode.
        """
        self.__command(ROVCommands.SYSTEM_MODE_STABILIZE)

    def update(self):
        """
        Processes notifications and dispatches events.

        Dispatches relevant ROV events based on queued notifications:

        * :class:`VehicleDisconnected` -> ``rov_vehicle_disconnected``
        * :class:`VehicleConnected` -> ``rov_vehicle_connected``
        * :class:`Armed` -> ``rov_armed``
        * :class:`Disarmed` -> ``rov_disarmed``
        * :class:`GainChange` -> ``rov_gain_change``
        * :class:`SystemModeChanged` -> ``rov_system_mode_changed``
        """
        while not self.__notification_queue.empty():
            notification = self.__notification_queue.get()

            if isinstance(notification, VehicleDisconnected):
                self.__dispatcher.dispatch("rov_vehicle_disconnected")
            elif isinstance(notification, VehicleConnected):
                self.__dispatcher.dispatch("rov_vehicle_connected")
            elif isinstance(notification, Armed):
                self.__dispatcher.dispatch("rov_armed")
            elif isinstance(notification, Disarmed):
                self.__dispatcher.dispatch("rov_disarmed")
            elif isinstance(notification, GainChange):
                self.__dispatcher.dispatch("rov_gain_change", notification.new_gain)
            elif isinstance(notification, SystemModeChanged):
                self.__dispatcher.dispatch("rov_system_mode_changed", notification.mode)
