from queue import PriorityQueue, Queue
import queue
import threading
from typing import Tuple
from numpy import interp
from core.event_dispatcher import EventDispatcher
from core.gcs_module import GCSModule
from core.logger import system_logger
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
from core.request_manager import RequestManager

__all__ = ["ROV"]


class Autopilot(GCSModule):
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
        super().__init__()

        self.__movement_queue: Queue[ROVMovement] = Queue(1)
        self.__command_queue: Queue[ROVCommands] = Queue(1)
        self.__notification_queue: PriorityQueue[ROVNotification] = PriorityQueue()
        
        self.__dispatcher = dispatcher
        
        self.__quit_event = threading.Event()
        self.__connection_daemon = AutopilotConnectionDaemon(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            base_ip,
            port,
            self.__quit_event,
        )
        self.__connection_daemon.start()

        self.__dispatcher.subscribe(
            "controller_button_down", self.__on_controller_button_down
        )
        self.__dispatcher.subscribe(
            "controller_joysticks", self.__handle_controller_joysticks
        )

    def __handle_controller_joysticks(self, movement: dict[str, Tuple[float, float]]):
        y, x, w, z = *movement["LJ"], *movement["RJ"]

        self.move(-x, y, -z, w, 0)

        system_logger.trace(f"{movement = }")

    def __move(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        """
        Queues a movement command.

        :param forward: Forward/backward value, ranging from -100 to 100.
        :type forward: float
        :param lateral: Lateral movement value, ranging from -100 to 100.
        :type lateral: float
        :param throttle: Vertical movement value, ranging from -100 to 100.
        :type throttle: float
        :param yaw: Yaw value, ranging from -100 to 100.
        :type yaw: float
        :param roll: Roll value, ranging from -100 to 100.
        :type roll: float
        """

        system_logger.debug(
            f"Sending movement command to daemon: forward {forward}, lateral {lateral}, throttle {throttle}, yaw {yaw}, roll {roll}"
        )
        try:
            self.__movement_queue.put(
                ROVMovement(forward, lateral, throttle, yaw, roll), block=False
            )
        except queue.Full:
            self.__movement_queue.get()
            self.__move(forward, lateral, throttle, yaw, roll)

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
                self.move(0, 0, 0, 0, 100.0)
            case "4":
                self.move(0, 0, 0, 0, -100.0)

    def __command(self, command: ROVCommands):
        """
        Queues a command for the autopilot.

        :param command: ROV command to be sent.
        :type command: ROVCommands
        """
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            self.__command_queue.get()
            self.__command(command)

    def quit(self):
        self.__quit_event.set()
        self.__connection_daemon.join()
                
    def status_ok(self) -> bool:
        return self.__connection_daemon.is_alive()

    def move(
        self,
        forward: float,
        lateral: float,
        throttle: float,
        yaw: float,
        roll: float,
        min_joy_value: float = -100.0,
        max_joy_value: float = 100.0,
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
