import queue
import multiprocessing
from hydranav.pi_admin.daemon import PiAdminDaemon
from hydranav.pi_admin.enums import AdminCommands
from hydranav.core import GCSModule, Updatable, request_manager, HasWebGUI


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

        self.__quit_event = multiprocessing.Event()
        self.__command_queue: multiprocessing.Queue[AdminCommands] = (
            multiprocessing.Queue(1)
        )
        self.__admin_daemon = PiAdminDaemon(
            self.__command_queue,
            self.__quit_event,
        )
        self.__admin_daemon.start()

        request_manager.register_handler("pi-admin/poweroff", self.poweroff)
        request_manager.register_handler("pi-admin/reboot", self.reboot)
        request_manager.register_handler(
            "pi-admin/restart/mavproxy", self.restart_mavproxy
        )
        request_manager.register_handler(
            "pi-admin/restart/manfaloty-bridge", self.restart_manfaloty_bridge
        )
        request_manager.register_handler(
            "pi-admin/restart/telemetry", self.restart_telemetry
        )
        request_manager.register_handler("pi-admin/restart/admin", self.restart_admin)
        request_manager.register_handler("mapper/PI_POWEROFF", self.poweroff)
        request_manager.register_handler("mapper/PI_REBOOT", self.reboot)

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
