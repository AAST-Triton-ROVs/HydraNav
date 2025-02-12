from queue import Queue
from threading import Thread
import time
from pymavlink import mavutil  # type: ignore

from logger import Logging
from rov.enums import ControlChannels, Directions, SystemModes
from rov.movement import Movement
from rov.command import Commands


MAX_BACKWARD_PWM = 1100
NEUTRAL_PWM = 1500
MAX_FORWARD_PWM = 1900
GAIN_LEVELS = (25, 40, 50, 75, 90)
TIME_OUT_SEC = 3


class ROVConnectionDaemon(Thread):
    """
    TODO:
    [x] Set gain
    [x] Move (by setting rc channels)
    [x] Send heartbeats
    [x] Stablize/destablize
    [x] Recieve ACK messages
    [ ] Configure Ardusub parameters (FS_GCS_ENABLE, FS_LEAK_ENABLE, FS_PILOT_INPUT, FS_PILOT_TIMEOUT) [Read/write parameters]
    [ ] Gripper Control
    [ ] Pixhwak sensor readings (pressure, velocity, aceleration, leakage)

    """

    def __init__(
        self,
        movement_queue: Queue[Movement],
        command_queue: Queue[Commands],
        ip: str,
        port: int,
        logging: Logging,
    ):
        super().__init__(daemon=True)
        self.__gain_index = 0
        self.__logging = logging

        self.__ip = ip
        self.__port = port

        self.__movement_queue: Queue[Movement] = movement_queue
        self.__command_queue: Queue[Commands] = command_queue

        self.__time_since_last_heartbeat = time.monotonic()

        self.__master = mavutil.mavlink_connection(f"udpin:{self.__ip}:{self.__port}")
        self.heartbeat()

        self.__logging.logger.info(
            f"ROVConnectionDaemon onnected to {self.__ip}:{self.__port}"
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

        self.__logging.logger.success("armed")

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

        self.__logging.logger.success("disarmed")

        return True

    def gain_up(self):
        if self.__gain_index + 1 < len(GAIN_LEVELS):
            self.__gain_index += 1

        self.__logging.logger.info("Gain up")

    def gain_down(self):
        if self.__gain_index - 1 >= 0:
            self.__gain_index -= 1

        self.__logging.logger.info("Gain down")

    def get_gain(self):
        return GAIN_LEVELS[self.__gain_index]

    def move(self, channel: ControlChannels, direction: Directions):
        rc_channel_values = [NEUTRAL_PWM for _ in range(8)]
        pwm = self.__percent_to_pwm(GAIN_LEVELS[self.__gain_index], direction)
        rc_channel_values[channel.value - 1] = pwm

        self.__logging.logger.debug(f"ROV {rc_channel_values = }")

        self.__master.mav.rc_channels_override_send(
            self.__master.target_system,
            self.__master.target_component,
            *rc_channel_values,
        )

        self.__logging.logger.info(
            f"{channel.name} is set to {pwm} in {direction.name} direction"
        )

    def heartbeat(self) -> bool:
        self.__master.mav.heartbeat_send(6, 8, 0, 0, 0)
        self.__logging.logger.info("Sent Heartbeat")

        response = self.__master.wait_heartbeat(timeout=TIME_OUT_SEC)
        if not response:
            return False
        self.__logging.logger.info("Recieved heartbeat")

        return True

    def set_system_mode(self, mode: SystemModes) -> bool:
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
                return False
            ack_msg = ack_msg.to_dict()

            if ack_msg["command"] != mavutil.mavlink.MAV_CMD_DO_SET_MODE:
                continue

            break

        self.__logging.logger.info(f"Set flight mode to {mode.name}")

        return True

    def run(self):
        previous_movement = None
        while True:
            if time.monotonic() - self.__time_since_last_heartbeat >= 0.9:
                if self.__movement_queue.empty() and previous_movement:
                    self.move(previous_movement.channel, previous_movement.direction)

                response = self.heartbeat()
                # TODO: IF THERE IS NOT HEARTBEAT RESPONSE, THEN PROBLEM WITH CONNECTION, REPORT THAT

                self.__time_since_last_heartbeat = time.monotonic()

            if not self.__movement_queue.empty():
                action = self.__movement_queue.get()

                if previous_movement != action:
                    self.move(action.channel, action.direction)
                    previous_movement = action

            if not self.__command_queue.empty():
                command = self.__command_queue.get()

                match command:
                    case Commands.ARM:
                        ack = self.arm()
                        # TODO: IF THERE IS NO ACK, THEN PROBLEM WITH CONNECTION, REPORT THAT
                    case Commands.DISARM:
                        ack = self.disarm()
                        # TODO: IF THERE IS NO ACK, THEN PROBLEM WITH CONNECTION, REPORT THAT
                    case Commands.SYSTEM_MODE_MANUAL:
                        ack = self.set_system_mode(SystemModes.MANUAL)
                        # TODO: IF THERE IS NO ACK, THEN PROBLEM WITH CONNECTION, REPORT THAT
                    case Commands.SYSTEM_MODE_STABILIZE:
                        ack = self.set_system_mode(SystemModes.STABILIZE)
                        # TODO: IF THERE IS NO ACK, THEN PROBLEM WITH CONNECTION, REPORT THAT
                    case Commands.GAIN_UP:
                        self.gain_up()
                    case Commands.GAIN_DOWN:
                        self.gain_down()
