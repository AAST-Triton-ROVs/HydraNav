from typing import Tuple
from admin.enums import AdminCommands
from logger import logging
from queue import Queue
from admin.daemon import PiAdminDaemon


class PiAdmin:
    """
    Manages administrative commands to the PiAdminDaemon.
    """

    def __init__(self, address: Tuple[str, int] = ("0.0.0.0", 2015)):
        """
        Initialize the PiAdmin object.

        :param address: The (IP address, port) tuple for the admin daemon.
        :type address: Tuple[str, int]
        """
        self.__admin_queue: Queue[AdminCommands] = Queue(1)
        self.__admin_daemon = PiAdminDaemon(self.__admin_queue, address)
        self.__admin_daemon.start()
        logging.logger.success("Admin daemon started")

    def poweroff(self):
        """
        Send poweroff command.
        """
        self.__admin_queue.put(AdminCommands.POWEROFF)

    def reboot(self):
        """
        Send reboot command.
        """
        self.__admin_queue.put(AdminCommands.REBOOT)

    def restart_mavproxy(self):
        """
        Send mavproxy restart command.
        """
        self.__admin_queue.put(AdminCommands.RESTART_MAVPROXY)

    def restart_gripper(self):
        """
        Send gripper restart command.
        """
        self.__admin_queue.put(AdminCommands.RESTART_GRIPPER)

    def restart_telemetry(self):
        """
        Send telemetry restart command.
        """
        self.__admin_queue.put(AdminCommands.RESTART_TELEMETRY)

    def restart_admin(self):
        """
        Send admin restart command.
        """
        self.__admin_queue.put(AdminCommands.RESTART_ADMIN)
