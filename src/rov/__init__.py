from queue import PriorityQueue, Queue
from typing import Tuple
from events import EventDispatcher
from logger import logging
from rov.daemon import ROVConnectionDaemon
from rov.enums import Directions, ControlChannels
from rov.gripper import Gripper
from rov.movement import ROVMovement
from rov.command import ROVCommands
from rov.notification import (
    Armed,
    Disarmed,
    GainChange,
    ROVNotification,
    SystemModeChanged,
    VehicleConnected,
    VehicleDisconnected,
)

__exports__ = ["ROV"]


class ROV:
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

        self.__connection_daemon = ROVConnectionDaemon(
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

    def __move(self, channel: ControlChannels, direction: Directions):
        self.__movement_queue.put(ROVMovement(channel, direction))

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

    def stop_movement(self):
        self.__move(ControlChannels.FORWARD, Directions.NEUTRAL)

    def move_roll_right(self):
        self.__move(ControlChannels.ROLL, Directions.POSITIVE)

    def move_roll_left(self):
        self.__move(ControlChannels.ROLL, Directions.NEGATIVE)

    def move_up(self):
        self.__move(ControlChannels.THROTTLE, Directions.POSITIVE)

    def move_down(self):
        self.__move(ControlChannels.THROTTLE, Directions.NEGATIVE)

    def move_yaw_right(self):
        self.__move(ControlChannels.YAW, Directions.POSITIVE)

    def move_yaw_left(self):
        self.__move(ControlChannels.YAW, Directions.NEGATIVE)

    def move_forward(self):
        self.__move(ControlChannels.FORWARD, Directions.POSITIVE)

    def move_backward(self):
        self.__move(ControlChannels.FORWARD, Directions.NEGATIVE)

    def move_lateral_right(self):
        self.__move(ControlChannels.LATERAL, Directions.POSITIVE)

    def move_lateral_left(self):
        self.__move(ControlChannels.LATERAL, Directions.NEGATIVE)

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
