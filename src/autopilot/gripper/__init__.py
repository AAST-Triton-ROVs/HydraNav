from queue import Queue
from logger import logging
from autopilot.enums import GripperCommands
from autopilot.gripper.daemon import GripperDaemon


class Gripper:
    def __init__(self, base_ip: str, pi_ip: str, port: int):
        self.__command_queue: Queue[GripperCommands] = Queue(1)
        self.__daemon = GripperDaemon(
            self.__command_queue,
            base_ip,
            pi_ip,
            port,
        )
        self.__daemon.start()
        logging.logger.success("Gripper daemon started")

    def reset(self):
        self.__command_queue.put(GripperCommands.RESET)
        logging.logger.success("Gripper reset")

    def open(self):
        self.__command_queue.put(GripperCommands.OPEN)
        logging.logger.success("Gripper open")

    def close(self):
        self.__command_queue.put(GripperCommands.CLOSE)
        logging.logger.success("Gripper close")

    def pitch_up(self):
        self.__command_queue.put(GripperCommands.PITCH_UP)
        logging.logger.success("Gripper pitch up")

    def pitch_down(self):
        self.__command_queue.put(GripperCommands.PITCH_DOWN)
        logging.logger.success("Gripper pitch down")

    def roll_right(self):
        self.__command_queue.put(GripperCommands.ROLL_RIGHT)
        logging.logger.success("Gripper roll right")

    def roll_left(self):
        self.__command_queue.put(GripperCommands.ROLL_LEFT)
        logging.logger.success("Gripper roll left")
