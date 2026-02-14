import multiprocessing
import queue
from typing import Tuple
from numpy import interp
from core import system_logger, GCSModule, event_dispatcher
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
from core import Updatable
from core import request_manager

__all__ = ["ROV"]


class Autopilot(GCSModule, Updatable):
    """
    Manages and controls the Pixhawk autopilot.

    Handles communication with the ROV, processes movement commands, sends control
    commands, and dispatches notifications. All commands are placed into thread-safe
    queues, read by :class:`AutopilotConnectionDaemon`.
    """

    def __init__(self):
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

        self.__movement_queue: multiprocessing.Queue[ROVMovement] = (
            multiprocessing.Queue(1)
        )
        self.__command_queue: multiprocessing.Queue[ROVCommands] = (
            multiprocessing.Queue(1)
        )
        self.__notification_queue: multiprocessing.Queue[ROVNotification] = (
            multiprocessing.Queue()
        )

        self.__quit_event = multiprocessing.Event()
        self.__connection_daemon = AutopilotConnectionDaemon(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            self.__quit_event,
        )
        self.__connection_daemon.start()

        event_dispatcher.subscribe("mapper/ARM", lambda _: self.arm())
        event_dispatcher.subscribe("mapper/DISARM", lambda _: self.disarm())
        event_dispatcher.subscribe("mapper/GAIN_UP", lambda _: self.gain_up())
        event_dispatcher.subscribe("mapper/GAIN_DOWN", lambda _: self.gain_down())
        event_dispatcher.subscribe(
            "mapper/hold/ROLL_RIGHT", lambda _: self.move(0, 0, 0, 0, 100)
        )
        event_dispatcher.subscribe(
            "mapper/hold/ROLL_LEFT", lambda _: self.move(0, 0, 0, 0, -100)
        )
        event_dispatcher.subscribe(
            "mapper/STABILIZATION_MODE", lambda _: self.flight_mode_stabilize()
        )
        event_dispatcher.subscribe(
            "mapper/MANUAL_MODE", lambda _: self.flight_mode_manual()
        )
        event_dispatcher.subscribe(
            "controller/joysticks", self.__handle_controller_joysticks
        )

        request_manager.register_handler("autopilot/arm", self.arm)
        request_manager.register_handler("autopilot/disarm", self.disarm)
        request_manager.register_handler("autopilot/gain-up", self.gain_up)
        request_manager.register_handler("autopilot/gain-down", self.gain_down)
        request_manager.register_handler(
            "autopilot/manual-flight", self.flight_mode_manual
        )
        request_manager.register_handler(
            "autopilot/stabilize-flight", self.flight_mode_stabilize
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
            return

    def __command(self, command: ROVCommands):
        """
        Queues a command for the autopilot.

        :param command: ROV command to be sent.
        :type command: ROVCommands
        """
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            return

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
        while True:
            try:
                notification = self.__notification_queue.get(block=False)
            except queue.Empty:
                return

            if isinstance(notification, VehicleDisconnected):
                event_dispatcher.dispatch("rov/vehicle_disconnected")
            elif isinstance(notification, VehicleConnected):
                event_dispatcher.dispatch("rov/vehicle_connected")
            elif isinstance(notification, Armed):
                event_dispatcher.dispatch("rov/armed")
            elif isinstance(notification, Disarmed):
                event_dispatcher.dispatch("rov/disarmed")
            elif isinstance(notification, GainChange):
                event_dispatcher.dispatch("rov/gain_change", notification.new_gain)
            elif isinstance(notification, SystemModeChanged):
                event_dispatcher.dispatch("rov/system_mode_changed", notification.mode)
