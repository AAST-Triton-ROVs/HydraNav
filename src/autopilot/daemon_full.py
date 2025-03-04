from queue import PriorityQueue, Queue
from threading import Thread
import time
from typing import Tuple
from numpy import interp
from pymavlink import mavutil  # type: ignore

from logger import logging
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


class AutopilotConnectionDaemonFull(Thread):
    """
    TODO:
    [x] Set gain
    [x] Move (by setting rc channels)
    [x] Send heartbeats
    [x] Stablize/destablize
    [x] Recieve ACK messages
    [X] Gripper Control
    [ ] Configure Ardusub parameters (FS_GCS_ENABLE, FS_LEAK_ENABLE, FS_PILOT_INPUT, FS_PILOT_TIMEOUT) [Read/write parameters]
    [ ] Pixhwak sensor readings (pressure, velocity, aceleration, leakage)

    """

    def __init__(
        self,
        movement_queue: Queue[ROVMovement],
        command_queue: Queue[ROVCommands],
        notification_queue: PriorityQueue[ROVNotification],
        base_ip: str,
        port: int
    ):
        super().__init__(daemon=True)
        self.__gain_index = 0

        self.__base_ip = base_ip
        self.__port = port

        self.__movement_queue: Queue[ROVMovement] = movement_queue
        self.__command_queue: Queue[ROVCommands] = command_queue
        self.__notification_queue: PriorityQueue[ROVNotification] = notification_queue

        self.__time_since_last_heartbeat = time.monotonic()
        self.__time_since_last_movement = time.monotonic()

        self.__master = mavutil.mavlink_connection(
            f"udpin:{self.__base_ip}:{self.__port}"
        )

    def __component_arm_disarm(self, act: int):
        """
        Send a command to arm or disarm the component.

        This method sends a MAVLink command to either arm or disarm the component
        of the vehicle. The command is sent using the `command_long_send` method
        of the MAVLink master object.

        :param act: Action to perform. Use 1 to arm the component and 0 to disarm it.
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

        This method takes a percentage value and a direction, and converts the 
        percentage to a PWM (Pulse Width Modulation) signal. The PWM signal is 
        calculated based on a neutral value and scaled by a factor of 400.

        :param percent: The percentage value to convert (0 to 100).
        :type percent: int
        :param direction: The direction of the PWM signal, which affects the 
                          sign of the resulting value.
        :type direction: Directions
        :return: The calculated PWM signal.
        :rtype: int
        """
        return NEUTRAL_PWM + int(percent / 100 * 400) * direction.value

    def __notify(self, notification: ROVNotification):
        """
        Sends a notification to the notification queue.

        :param notification: The notification to be sent.
        :type notification: ROVNotification
        """
        self.__notification_queue.put(notification)

    def arm(self) -> bool:
        """
        Arms the autopilot component.

        This method sends a command to arm the autopilot component and waits for an acknowledgment
        message indicating the success of the operation. If the acknowledgment message is received
        and confirms the arming command, the method logs a success message and returns True.
        If the acknowledgment message is not received within the specified timeout, the method
        returns False.

        :return: True if the autopilot component is successfully armed, False otherwise.
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

        logging.logger.success("armed")

        return True

    def disarm(self) -> bool:
        """
        Disarms the vehicle by sending a disarm command to the autopilot.

        This method sends a disarm command to the autopilot and waits for an acknowledgment
        message indicating that the command has been received and processed. If the acknowledgment
        message is received and indicates that the disarm command was successful, the method
        logs a success message and returns True. If the acknowledgment message is not received
        within the specified timeout period, the method returns False.

        :return: True if the vehicle was successfully disarmed, False otherwise.
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

        logging.logger.success("disarmed")

        return True

    def gain_up(self):
        """
        Increase the gain index by one level if it is not already at the maximum level.

        This method increments the internal gain index by one, provided that the 
        current gain index is less than the length of the GAIN_LEVELS list minus one.
        It also logs an informational message indicating that the gain has been increased.
        """
        if self.__gain_index + 1 < len(GAIN_LEVELS):
            self.__gain_index += 1

        logging.logger.info("Gain up")

    def gain_down(self):
        """
        Decreases the gain index by one if it is greater than zero.

        This method checks if the current gain index is greater than zero and, if so, 
        decrements the gain index by one. It also logs the action of decreasing the gain.

        :raises AttributeError: If the gain index attribute is not found.
        """
        if self.__gain_index - 1 >= 0:
            self.__gain_index -= 1

        logging.logger.info("Gain down")

    def get_gain(self):
        """
        Retrieve the current gain level.

        :return: The current gain level from the GAIN_LEVELS list.
        :rtype: int or float
        """
        return GAIN_LEVELS[self.__gain_index]

    def __get_scaled_pwm(self, value: float) -> int:
        """
        Convert a given float value to a scaled PWM (Pulse Width Modulation) signal.

        The method determines the direction based on the sign of the input value and
        scales the absolute value to a PWM signal using predefined gain levels.

        :param value: The input value to be converted, ranging from -1.0 to 1.0.
        :type value: float
        :return: The scaled PWM signal as an integer.
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

    def move(
        self, forward: float, lateral: float, throttle: float, yaw: float, roll: float
    ):
        """
        Move the ROV (Remotely Operated Vehicle) by setting the PWM values for various control channels.

        :param forward: The forward movement value, scaled to PWM.
        :type forward: float
        :param lateral: The lateral movement value, scaled to PWM.
        :type lateral: float
        :param throttle: The throttle value, scaled to PWM.
        :type throttle: float
        :param yaw: The yaw movement value, scaled to PWM.
        :type yaw: float
        :param roll: The roll movement value, scaled to PWM.
        :type roll: float

        :return: None
        :rtype: None

        This method calculates the PWM values for the given movement parameters and sends them to the ROV's control channels.
        It also logs the PWM values for debugging and informational purposes.
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

        logging.logger.debug(f"ROV {rc_channel_values = }")

        self.__master.mav.rc_channels_override_send(
            self.__master.target_system,
            self.__master.target_component,
            *rc_channel_values,
        )

        logging.logger.info(
            f"Moved ROV with values: forward={forward_pwm}, lateral={lateral_pwm}, throttle={throttle_pwm}, yaw={yaw_pwm}, roll={roll_pwm}"
        )

    def recieve_heartbeat(self) -> bool:
        """
        Waits for a heartbeat signal from the master and logs the event.

        This method waits for a heartbeat signal from the master with a specified timeout.
        If a heartbeat is received within the timeout period, it logs the event and returns True.
        If no heartbeat is received, it returns False.

        :return: True if a heartbeat is received, False otherwise.
        :rtype: bool
        """
        response = self.__master.wait_heartbeat(timeout=TIME_OUT_SEC)
        if response is None:
            return False
        logging.logger.info("Recieved heartbeat")

        return True

    def send_heartbeat(self):
        """
        Sends a heartbeat message to the MAVLink master.

        This method sends a heartbeat message with predefined parameters to 
        the MAVLink master to indicate that the autopilot is alive and functioning.
        It also logs the action for debugging purposes.

        :return: None
        """
        self.__master.mav.heartbeat_send(6, 8, 0, 0, 0)
        logging.logger.info("Sent Heartbeat")

    def set_system_mode(self, mode: SystemModes) -> bool:
        """
        Set the system mode of the autopilot.
        This function sends a command to the autopilot to change its flight mode
        to the specified mode. It waits for an acknowledgment from the autopilot
        to confirm that the mode has been set successfully.
        
        :param mode: The desired system mode to set.
        :type mode: SystemModes
        :return: True if the mode was set successfully, False otherwise.
        :rtype: bool
        """
        
        self.__master.mav.set_mode_send(
            self.__master.target_system,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            mode.value,
        )

        while True:
            ack_msg = self.__master.recv_match(
                type="COMMAND_ACK", blocking=True, timeout=TIME_OUT_SEC
            )
            if not ack_msg:
                logging.logger.error(f"Setting flight mode `{mode.name}` failed")
                return False
            ack_msg = ack_msg.to_dict()

            if (
                ack_msg["command"] != 11
                and ack_msg["command"] != mavutil.mavlink.MAV_CMD_DO_SET_MODE
            ):
                continue

            logging.logger.success(f"Set flight mode to {mode.name}")
            return True

    def run(self):
        """
        Main loop that handles the autopilot's operations.

        This method continuously performs the following tasks:
        1. Sends and receives heartbeats to monitor the connection status with the vehicle.
        2. Processes movement actions from the movement queue and commands from the command queue.

        Heartbeat:
        - Sends a heartbeat signal if the time since the last heartbeat exceeds 0.9 seconds.
        - Receives a heartbeat response and updates the connection status.
        - Notifies the system if the vehicle is connected or disconnected.

        Movement:
        - Retrieves and executes movement actions from the movement queue.
        - Ensures actions are executed if they differ from the previous action or if the time since the last movement exceeds 0.9 seconds.

        Commands:
        - Retrieves and executes commands from the command queue using pattern matching.
        - Supported commands include arming/disarming the vehicle, changing system modes, and adjusting gain levels.

        Notifications:
        - Notifies the system of various events such as vehicle connection status, system mode changes, and gain changes.
        """
        previous_movement = None
        is_connected = False
        while True:
            if time.monotonic() - self.__time_since_last_heartbeat >= 0.9:
                self.send_heartbeat()

                response = self.recieve_heartbeat()
                if response and not is_connected:
                    self.__notify(VehicleConnected())
                    is_connected = True

                if not response:
                    is_connected = False
                    self.__notify(VehicleDisconnected())
                    logging.logger.critical(
                        "No heartbeat from vehicle; Vehicle disconnected or unresponsive"
                    )

                self.__time_since_last_heartbeat = time.monotonic()

            if not self.__movement_queue.empty():
                action = self.__movement_queue.get()

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

            if not self.__command_queue.empty():
                command = self.__command_queue.get()

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
