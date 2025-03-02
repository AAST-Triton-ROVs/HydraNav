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
        address: Tuple[str, int],
    ):
        super().__init__(daemon=True)
        self.__gain_index = 0

        self.__address = address

        self.__movement_queue: Queue[ROVMovement] = movement_queue
        self.__command_queue: Queue[ROVCommands] = command_queue
        self.__notification_queue: PriorityQueue[ROVNotification] = notification_queue

        self.__time_since_last_heartbeat = time.monotonic()
        self.__time_since_last_movement = time.monotonic()

        self.__master = mavutil.mavlink_connection(
            f"udpin:{self.__address[0]}:{self.__address[1]}"
        )

    def __component_arm_disarm(self, act: int):
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
        return NEUTRAL_PWM + int(percent / 100 * 400) * direction.value

    def __notify(self, notification: ROVNotification):
        self.__notification_queue.put(notification)

    def arm(self) -> bool:
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
        if self.__gain_index + 1 < len(GAIN_LEVELS):
            self.__gain_index += 1

        logging.logger.info("Gain up")

    def gain_down(self):
        if self.__gain_index - 1 >= 0:
            self.__gain_index -= 1

        logging.logger.info("Gain down")

    def get_gain(self):
        return GAIN_LEVELS[self.__gain_index]

    def __get_scaled_pwm(self, value: float) -> int:
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
        response = self.__master.wait_heartbeat(timeout=TIME_OUT_SEC)
        if response is None:
            return False
        logging.logger.info("Recieved heartbeat")

        return True

    def send_heartbeat(self):
        self.__master.mav.heartbeat_send(6, 8, 0, 0, 0)
        logging.logger.info("Sent Heartbeat")

    def set_system_mode(self, mode: SystemModes) -> bool:
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
