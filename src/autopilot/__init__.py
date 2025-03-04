from queue import PriorityQueue, Queue
from typing import Tuple
from events import EventDispatcher
from numpy import interp
from autopilot.daemon_full import AutopilotConnectionDaemonFull
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
        base_ip: str = "0.0.0.0", 
        port: int = 2000,
    ):
        self.__movement_queue: Queue[ROVMovement] = Queue(1)
        self.__command_queue: Queue[ROVCommands] = Queue(1)
        self.__notification_queue: PriorityQueue[ROVNotification] = PriorityQueue()

        self.__dispatcher = dispatcher

        self.__connection_daemon = AutopilotConnectionDaemonFull(
            self.__movement_queue,
            self.__command_queue,
            self.__notification_queue,
            base_ip,
            port,
        )
        self.__connection_daemon.start()

    def __move(self,  forward: float, lateral: float, throttle: float, yaw: float, roll: float):
        """
        Move the ROV by adding a movement command to the movement queue.

        :param forward: The forward movement value.
        :type forward: float
        :param lateral: The lateral movement value.
        :type lateral: float
        :param throttle: The throttle value.
        :type throttle: float
        :param yaw: The yaw movement value.
        :type yaw: float
        :param roll: The roll movement value.
        :type roll: float
        """
        self.__movement_queue.put(ROVMovement(forward, lateral, throttle, yaw, roll))
        
    def move(self, forward: float, lateral: float, throttle: float, yaw: float, roll: float, min_joy_value: int =  -100, max_joy_value: int = 100):
        def move(self, forward: float, lateral: float, throttle: float, yaw: float, roll: float, min_joy_value: int = -100, max_joy_value: int = 100):
            """
            Move the vehicle based on joystick inputs.

            This method interprets the joystick inputs and maps them to the vehicle's movement commands.

            :param forward: Joystick input for forward/backward movement.
            :type forward: float
            :param lateral: Joystick input for lateral (left/right) movement.
            :type lateral: float
            :param throttle: Joystick input for throttle (up/down) movement.
            :type throttle: float
            :param yaw: Joystick input for yaw (rotation around vertical axis).
            :type yaw: float
            :param roll: Joystick input for roll (rotation around longitudinal axis).
            :type roll: float
            :param min_joy_value: Minimum joystick value, defaults to -100.
            :type min_joy_value: int, optional
            :param max_joy_value: Maximum joystick value, defaults to 100.
            :type max_joy_value: int, optional
            """
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
        """
        Process notifications from the notification queue and dispatch corresponding events.
        This method continuously checks the notification queue for new notifications. 
        Depending on the type of notification, it dispatches the appropriate event 
        using the dispatcher.
        Notifications and their corresponding dispatched events:
        - VehicleDisconnected: Dispatches "rov_vehicle_disconnected"
        - VehicleConnected: Dispatches "rov_vehicle_connected"
        - Armed: Dispatches "rov_armed"
        - Disarmed: Dispatches "rov_disarmed"
        - GainChange: Dispatches "rov_gain_change" with the new gain value
        - SystemModeChanged: Dispatches "rov_system_mode_changed" with the new mode
        
        :raises queue.Empty: If the notification queue is empty.
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
