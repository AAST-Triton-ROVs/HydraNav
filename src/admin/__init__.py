from typing import Tuple
from logger import logging
from queue import Queue
from admin.daemon import PiAdminDaemon


class PiAdmin:
    def __init__(self, address: Tuple[str, int] = ("0.0.0.0", 2015)):
        self.__admin_queue: Queue[int] = Queue(1)
        self.__admin_daemon = PiAdminDaemon(self.__admin_queue, address)
        self.__admin_daemon.start()
        logging.logger.success("Admin daemon started")

    def poweroff(self):
        self.__admin_queue.put(0)
        logging.logger.success("Powering off")

    def reboot(self):
        self.__admin_queue.put(1)
        logging.logger.success("Rebooting")

    def restart_mavproxy(self):
        self.__admin_queue.put(2)
        logging.logger.success("Restarting mavproxy service")

    def restart_gripper(self):
        self.__admin_queue.put(3)
        logging.logger.success("Restarting gripper service")

    def restart_telemetry(self):
        self.__admin_queue.put(4)
        logging.logger.success("Restarting telemetry service")

    def restart_admin(self):
        self.__admin_queue.put(10)
        logging.logger.success("Restarting admin service")
