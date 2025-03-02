from queue import PriorityQueue, Queue
from typing import Tuple
from events import EventDispatcher
from numpy import interp
from autopilot.daemon_full import AutopilotConnectionDaemonFull
from autopilot.gripper import Gripper
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
    def __init__(
        self,
        dispatcher: EventDispatcher,
        address: Tuple[str, int] = ("0.0.0.0", 2000),
        gripper_address: Tuple[str, int] = ("192.168.1.100", 2005),
    ):
        self.__movement_queue: Queue[ROVMovement] = Queue(1)
        self.__command_queue: Queue[ROVCommands] = Queue(1)
        self.__notification_queue: PriorityQueue[ROVNotification] = PriorityQueue()

        self.__dispatcher = dispatcher

        self.__connection_daemon = AutopilotConnectionDaemonFull(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            address,
        )
        self.__connection_daemon.start()

        self.gripper = Gripper(
            address[0],
            gripper_address[0],
            gripper_address[1],
        )

    def __move(self,  forward: float, lateral: float, throttle: float, yaw: float, roll: float):
        self.__movement_queue.put(ROVMovement(forward, lateral, throttle, yaw, roll))
        
    def move(self, forward: float, lateral: float, throttle: float, yaw: float, roll: float, min_joy_value: int =  -100, max_joy_value: int = 100):
        self.__move(
            interp(forward, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(lateral, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(throttle, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(yaw, [min_joy_value, max_joy_value], [-1.0, 1.0]),
            interp(roll, [min_joy_value, max_joy_value], [-1.0, 1.0]),
        )

    def __command(self, command: ROVCommands):
        self.__command_queue.put(command)

    def gain_up(self):
        self.__command(ROVCommands.GAIN_UP)

    def gain_down(self):
        self.__command(ROVCommands.GAIN_DOWN)

    def arm(self):
        self.__command(ROVCommands.ARM)

    def disarm(self):
        self.__command(ROVCommands.DISARM)

    def flight_mode_manual(self):
        self.__command(ROVCommands.SYSTEM_MODE_MANUAL)

    def flight_mode_stabilize(self):
        self.__command(ROVCommands.SYSTEM_MODE_STABILIZE)

    def update(self):
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
