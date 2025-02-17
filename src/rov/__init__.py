from queue import PriorityQueue, Queue
from typing import Tuple
from events import EventDispatcher
from logger import Logging
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
        logging: Logging,
        ip: str = "0.0.0.0",
        port: int = 2000,
        gripper_port: int = 2500,
    ):
        self.__movement_queue: Queue[ROVMovement] = Queue(1)
        self.__command_queue: Queue[ROVCommands] = Queue(1)
        self.__notification_queue: PriorityQueue[ROVNotification] = PriorityQueue()

        self.__dispatcher = dispatcher
        self.__logging = logging
        self.__ip = ip
        self.__port = port

        self.__connection_daemon = ROVConnectionDaemon(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            self.__ip,
            self.__port,
            self.__logging,
        )
        self.__connection_daemon.start()

        self.gripper = Gripper(self.__logging, self.__ip, gripper_port)

        self.__dispatcher.subscribe("controller_joysticks", self.__handle_joysticks)

    def __handle_joysticks(self, move: Tuple[float, float, float, float]):
        x, y, z, w = move

        if x == y == z == w == 0:
            self.stop_movement()
            return

        if x > y:
            if y > 0:
                self.move_lateral_right()
            elif y < 0:
                self.move_forward()
        else:
            if x > 0:  # joystick to the bottom
                self.move_backward()
            elif x < 0:
                self.move_lateral_left()

        if z > w:
            if z > 0:  # joystick to the left
                self.move_yaw_right()
            elif z < 0:
                self.move_up()
        else:
            if w > 0:  # joystick to the bottom
                self.move_down()
            elif w < 0:
                self.move_yaw_left()

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
