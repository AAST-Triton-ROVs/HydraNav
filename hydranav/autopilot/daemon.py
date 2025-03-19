from queue import PriorityQueue, Queue
import queue
from threading import Thread
import threading
import time
from numpy import interp
from pymavlink import mavutil  # type: ignore

from core.logger import system_logger
from autopilot.enums import ControlChannels, Directions, SystemModes
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


MAX_BACKWARD_PWM = 1100
NEUTRAL_PWM = 1500
MAX_FORWARD_PWM = 1900
GAIN_LEVELS = (25, 40, 50, 75, 90)
TIME_OUT_SEC = 2


class AutopilotConnectionDaemon(Thread):
    """
    AutopilotConnectionDaemon for controlling the ROV.

    :TODO:
        - Configure Ardusub parameters
        - PixhawK sensor readings
    """

    def __init__(
        self,
        movement_queue: Queue[ROVMovement],
        command_queue: Queue[ROVCommands],
        notification_queue: PriorityQueue[ROVNotification],
        base_ip: str,
        port: int,
        quit_event: threading.Event,
    ):
        """
        Initialize the daemon.

        :param movement_queue: Queue for ROVMovement objects.
        :type movement_queue: Queue
        :param command_queue: Queue for ROVCommands.
        :type command_queue: Queue
        :param notification_queue: PriorityQueue for notifications.
        :type notification_queue: PriorityQueue
        :param base_ip: IP address of the MAVLink master.
        :type base_ip: str
        :param port: Port number for the MAVLink connection.
        :type port: int
        """
        super().__init__(daemon=True)
        self.__gain_index = 0

        self.__base_ip = base_ip
        self.__port = port

        self.__movement_queue: Queue[ROVMovement] = movement_queue
        self.__command_queue: Queue[ROVCommands] = command_queue
        self.__notification_queue: PriorityQueue[ROVNotification] = notification_queue

        self.__time_since_last_heartbeat = time.monotonic()
        self.__time_since_last_movement = time.monotonic()
        
        self.__quit_event = quit_event

        self.__master = mavutil.mavlink_connection(
            f"udpin:{self.__base_ip}:{self.__port}"
        )

    def __component_arm_disarm(self, act: int):
        """
        Send a command to arm or disarm the component.

        :param act: Action (1 to arm, 0 to disarm).
        :type act: int
        """
        self.__master.mav.command_long_send(
            self.__master.target_system,
            self.__master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            act,
            0,
            0,
            0,
            0,
            0,
            0,
        )

    def __percent_to_pwm(self, percent: int, direction: Directions) -> int:
        """
        Convert a percentage value to a PWM signal.

        :param percent: 0 to 100 percentage value.
        :type percent: int
        :param direction: Direction of PWM (positive, negative, or neutral).
        :type direction: Directions
        :return: PWM signal as int.
        :rtype: int
        """
        return NEUTRAL_PWM + int(percent / 100 * 400) * direction.value

    def __get_scaled_pwm(self, value: float) -> int:
        """
        Convert a float value to a scaled PWM signal.

        :param value: Float from -1.0 to 1.0.
        :type value: float
        :return: Scaled PWM value.
        :rtype: int
        """
        if value > 0:
            direction = Directions.POSITIVE
        elif value < 0:
            direction = Directions.NEGATIVE
        else:
            direction = Directions.NEUTRAL

        return self.__percent_to_pwm(
            int(interp(abs(value), [0, 1.0], [0, GAIN_LEVELS[self.__gain_index]])),
            direction,
        )

    def __notify(self, notification: ROVNotification):
        """
        Add a notification to the queue.

        :param notification: ROVNotification to send.
        :type notification: ROVNotification
        """
        try:
            self.__notification_queue.put(notification, block=False)
        except queue.Full:
            system_logger.error("Unable to put notification in queue")
            return

    def arm(self) -> bool:
        """
        Arm the autopilot component.

        :return: True if the autopilot is armed, False otherwise.
        :rtype: bool
        """
        self.__component_arm_disarm(1)

        while True:
            ack_msg = self.__master.recv_match(
                type="COMMAND_ACK", blocking=True, timeout=TIME_OUT_SEC
            )
            if not ack_msg:
                return False

            ack_msg = ack_msg.to_dict()
            if ack_msg["command"] != mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                continue
            break

        system_logger.success("armed")
        return True

    def disarm(self) -> bool:
        """
        Disarm the autopilot.

        :return: True if the vehicle is disarmed, False otherwise.
        :rtype: bool
        """
        self.__component_arm_disarm(0)

        while True:
            ack_msg = self.__master.recv_match(
                type="COMMAND_ACK", blocking=True, timeout=TIME_OUT_SEC
            )
            if not ack_msg:
                return False

            ack_msg = ack_msg.to_dict()
            if ack_msg["command"] != mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                continue
            break

        system_logger.success("disarmed")
        return True

    def gain_up(self):
        """
        Increase the gain level by one step (if not at max).
        """
        if self.__gain_index + 1 < len(GAIN_LEVELS):
            self.__gain_index += 1

        system_logger.info("Gain up")

    def gain_down(self):
        """
        Decrease the gain level by one step (if not at min).
        """
        if self.__gain_index - 1 >= 0:
            self.__gain_index -= 1

        system_logger.info("Gain down")

    def get_gain(self):
        """
        Get current gain level.

        :return: Gain level as int from GAIN_LEVELS.
        :rtype: int
        """
        return GAIN_LEVELS[self.__gain_index]

    def move(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        """
        Move the ROV by sending PWM values to control channels.

        :param forward: Forward movement (-1.0 to 1.0).
        :type forward: float
        :param lateral: Lateral movement (-1.0 to 1.0).
        :type lateral: float
        :param throttle: Vertical movement (-1.0 to 1.0).
        :type throttle: float
        :param yaw: Yaw movement (-1.0 to 1.0).
        :type yaw: float
        :param roll: Roll movement (-1.0 to 1.0).
        :type roll: float
        :return: None
        """
        rc_channel_values = [NEUTRAL_PWM for _ in range(8)]

        forward_pwm = self.__get_scaled_pwm(forward)
        rc_channel_values[ControlChannels.FORWARD.value - 1] = forward_pwm

        lateral_pwm = self.__get_scaled_pwm(lateral)
        rc_channel_values[ControlChannels.LATERAL.value - 1] = lateral_pwm

        throttle_pwm = self.__get_scaled_pwm(throttle)
        rc_channel_values[ControlChannels.THROTTLE.value - 1] = throttle_pwm

        yaw_pwm = self.__get_scaled_pwm(yaw)
        rc_channel_values[ControlChannels.YAW.value - 1] = yaw_pwm

        roll_pwm = self.__get_scaled_pwm(roll)
        rc_channel_values[ControlChannels.ROLL.value - 1] = roll_pwm

        system_logger.debug(f"ROV {rc_channel_values = }")

        self.__master.mav.rc_channels_override_send(
            self.__master.target_system,
            self.__master.target_component,
            *rc_channel_values,
        )

        system_logger.info(
            f"Moved ROV with values: forward={forward_pwm}, lateral={lateral_pwm}, throttle={throttle_pwm}, yaw={yaw_pwm}, roll={roll_pwm}"
        )

    def recieve_heartbeat(self) -> bool:
        """
        Wait for a heartbeat from the master.

        :return: True if received, False otherwise.
        :rtype: bool
        """
        response = self.__master.wait_heartbeat(timeout=TIME_OUT_SEC)
        if response is None:
            return False
        system_logger.info("Recieved heartbeat")
        return True

    def send_heartbeat(self):
        """
        Send a heartbeat to the MAVLink master.
        """
        self.__master.mav.heartbeat_send(6, 8, 0, 0, 0)
        system_logger.info("Sent Heartbeat")

    def set_system_mode(self, mode: SystemModes) -> bool:
        """
        Set the autopilot's flight mode.

        :param mode: Desired SystemMode.
        :type mode: SystemModes
        :return: True if mode is set successfully, False otherwise.
        :rtype: bool
        """
        self.__master.mav.set_mode_send(
            self.__master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode.value,
        )

        while True:
            ack_msg = self.__master.recv_match(
                type="COMMAND_ACK", blocking=True, timeout=TIME_OUT_SEC
            )
            if not ack_msg:
                system_logger.error(f"Setting flight mode `{mode.name}` failed")
                return False

            ack_msg = ack_msg.to_dict()
            if (
                ack_msg["command"] != 11
                and ack_msg["command"] != mavutil.mavlink.MAV_CMD_DO_SET_MODE
            ):
                continue

            system_logger.success(f"Set flight mode to {mode.name}")
            return True

    def run(self):
        """
        Main loop for autopilot operations.

        1. Send/receive heartbeats to monitor connection.
        2. Handle movement from movement_queue.
        3. Handle commands from command_queue.
        """
        previous_movement = None
        is_connected = False
        while not self.__quit_event.is_set():
            if time.monotonic() - self.__time_since_last_heartbeat >= 0.9:
                self.send_heartbeat()

                response = self.recieve_heartbeat()
                if response and not is_connected:
                    self.__notify(VehicleConnected())
                    is_connected = True

                if not response:
                    is_connected = False
                    self.__notify(VehicleDisconnected())
                    system_logger.critical(
                        "No heartbeat from vehicle; Vehicle disconnected or unresponsive"
                    )

                self.__time_since_last_heartbeat = time.monotonic()

            try:
                action = self.__movement_queue.get(block=False)
            except queue.Empty:
                pass
            else:
                if (
                    previous_movement != action
                    or time.monotonic() - self.__time_since_last_movement >= 0.9
                ):
                    self.move(
                        action.forward,
                        action.lateral,
                        action.throttle,
                        action.yaw,
                        action.roll,
                    )
                    previous_movement = action
                    self.__time_since_last_movement = time.monotonic()

            try:
                command = self.__command_queue.get(block=False)
            except queue.Empty:
                pass
            else:
                match command:
                    case ROVCommands.ARM:
                        ack = self.arm()
                        if ack:
                            self.__notify(Armed())

                    case ROVCommands.DISARM:
                        ack = self.disarm()
                        if ack:
                            self.__notify(Disarmed())

                    case ROVCommands.SYSTEM_MODE_MANUAL:
                        ack = self.set_system_mode(SystemModes.MANUAL)
                        if ack:
                            self.__notify(SystemModeChanged(SystemModes.MANUAL))

                    case ROVCommands.SYSTEM_MODE_STABILIZE:
                        ack = self.set_system_mode(SystemModes.STABILIZATION)
                        if ack:
                            self.__notify(SystemModeChanged(SystemModes.STABILIZATION))

                    case ROVCommands.GAIN_UP:
                        self.gain_up()
                        self.__notify(GainChange(GAIN_LEVELS[self.__gain_index]))

                    case ROVCommands.GAIN_DOWN:
                        self.gain_down()
                        self.__notify(GainChange(GAIN_LEVELS[self.__gain_index]))
