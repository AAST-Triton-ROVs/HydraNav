import queue
import threading
from typing import Tuple
from queue import Queue
from core import Updatable
from hydranav.core import request_manager
from pi_admin.daemon import PiAdminDaemon
from pi_admin.enums import AdminCommands
from core import GCSModule


class PiAdmin(GCSModule, Updatable):
    """
    Manages administrative commands to the PiAdminDaemon.
    """

    def __init__(
        self,
    ):
        """
        Initialize the PiAdmin object.

        :param address: The (IP address, port) tuple for the admin daemon.
        :type address: Tuple[str, int]
        """
        super().__init__()

        self.__quit_event = threading.Event()
        self.__command_queue: Queue[AdminCommands] = Queue(1)
        self.__admin_daemon = PiAdminDaemon(
            self.__command_queue,
            self.__quit_event,
        )
        self.__admin_daemon.start()
        
        request_manager.register_handler("pi-admin/poweroff")
        request_manager.register_handler("pi-admin/reboot")
        request_manager.register_handler("pi-admin/restart/mavproxy")
        request_manager.register_handler("pi-admin/restart/manfaloty-bridge")
        request_manager.register_handler("pi-admin/restart/telemetry")
        request_manager.register_handler("pi-admin/restart/admin")

    def __send_command(self, command: AdminCommands):
        try:
            self.__command_queue.put(command, block=False)
        except queue.Full:
            return
        
    def update(self):
        return 

    def status_ok(self) -> bool:
        return self.__admin_daemon.is_alive()

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

    def restart_manfaloty_bridge(self):
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
