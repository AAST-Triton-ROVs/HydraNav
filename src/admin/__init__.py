import queue
import threading
from typing import Tuple
from admin.enums import AdminCommands
from core.event_dispatcher import EventDispatcher
from core.gcs_module import GCSModule
from core.logger import system_logger
from queue import Queue
from admin.daemon import PiAdminDaemon
from core.request_manager import RequestManager


class PiAdmin(GCSModule):
    """
    Manages administrative commands to the PiAdminDaemon.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        request_manager: RequestManager,
        address: Tuple[str, int] = ("0.0.0.0", 2015),
    ):
        """
        Initialize the PiAdmin object.

        :param address: The (IP address, port) tuple for the admin daemon.
        :type address: Tuple[str, int]
        """
        super().__init__(dispatcher, request_manager)

        self.__quit_event = threading.Event()
        self.__command_queue: Queue[AdminCommands] = Queue(1)
        self.__admin_daemon = PiAdminDaemon(
            self.__command_queue, address, self.__quit_event
        )
        self.__admin_daemon.start()
        system_logger.success("Admin daemon started")

    def __send_command(self, command: AdminCommands):
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            self.__command_queue.get()
            self.__send_command(command)

    def quit(self):
        self.__quit_event.set()
        self.__admin_daemon.join()

    def poweroff(self):
        """
        Send poweroff command.
        """
        self.__send_command(AdminCommands.POWEROFF)

    def reboot(self):
        """
        Send reboot command.
        """
        self.__send_command(AdminCommands.REBOOT)

    def restart_mavproxy(self):
        """
        Send mavproxy restart command.
        """
        self.__send_command(AdminCommands.RESTART_MAVPROXY)

    def restart_gripper(self):
        """
        Send gripper restart command.
        """
        self.__send_command(AdminCommands.RESTART_GRIPPER)

    def restart_telemetry(self):
        """
        Send telemetry restart command.
        """
        self.__send_command(AdminCommands.RESTART_TELEMETRY)

    def restart_admin(self):
        """
        Send admin restart command.
        """
        self.__send_command(AdminCommands.RESTART_ADMIN)
