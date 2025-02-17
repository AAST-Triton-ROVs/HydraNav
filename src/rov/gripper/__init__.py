from queue import Queue
from logger import Logging
from rov.enums import GripperCommands
from rov.gripper.daemon import GripperDaemon


class Gripper:
    def __init__(self, logging: Logging, ip: str = "0.0.0.0", port: int = 2500):
        self.__gripper_queue: Queue[GripperCommands] = Queue(1)
        self.__logging = logging
        self.__gripper_daemon = GripperDaemon(
            self.__gripper_queue, self.__logging, ip, port
        )
        self.__gripper_daemon.start()
        self.__logging.logger.success("Gripper daemon started")

    def reset(self):
        self.__gripper_queue.put(GripperCommands.RESET)
        self.__logging.logger.success("Gripper reset")

    def open(self):
        self.__gripper_queue.put(GripperCommands.OPEN)
        self.__logging.logger.success("Gripper open")

    def close(self):
        self.__gripper_queue.put(GripperCommands.CLOSE)
        self.__logging.logger.success("Gripper close")

    def pitch_up(self):
        self.__gripper_queue.put(GripperCommands.PITCH_UP)
        self.__logging.logger.success("Gripper pitch up")

    def pitch_down(self):
        self.__gripper_queue.put(GripperCommands.PITCH_DOWN)
        self.__logging.logger.success("Gripper pitch down")

    def roll_right(self):
        self.__gripper_queue.put(GripperCommands.ROLL_RIGHT)
        self.__logging.logger.success("Gripper roll right")

    def roll_left(self):
        self.__gripper_queue.put(GripperCommands.ROLL_LEFT)
        self.__logging.logger.success("Gripper roll left")
