from typing import Tuple
from admin.enums import AdminCommands
from logger import logging
from queue import Queue
from admin.daemon import PiAdminDaemon


class PiAdmin:
    def __init__(self, address: Tuple[str, int] = ("0.0.0.0", 2015)):
        self.__admin_queue: Queue[AdminCommands] = Queue(1)
        self.__admin_daemon = PiAdminDaemon(self.__admin_queue, address)
        self.__admin_daemon.start()
        logging.logger.success("Admin daemon started")

    def poweroff(self):
        self.__admin_queue.put(AdminCommands.POWEROFF)

    def reboot(self):
        self.__admin_queue.put(AdminCommands.REBOOT)

    def restart_mavproxy(self):
        self.__admin_queue.put(AdminCommands.RESTART_MAVPROXY)

    def restart_gripper(self):
        self.__admin_queue.put(AdminCommands.RESTART_GRIPPER)

    def restart_telemetry(self):
        self.__admin_queue.put(AdminCommands.RESTART_TELEMETRY)

    def restart_admin(self):
        self.__admin_queue.put(AdminCommands.RESTART_ADMIN)
