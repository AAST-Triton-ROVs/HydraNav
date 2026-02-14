import queue
import multiprocessing
from hydranav.pi_admin.daemon import PiAdminDaemon
from hydranav.pi_admin.enums import AdminCommands
from hydranav.core import GCSModule, Updatable, request_manager, HasWebGUI
from nicegui import ui


class PiAdmin(GCSModule, Updatable, HasWebGUI):
    """
    Manages administrative commands to the PiAdminDaemon.
    """

    def __init__(self):
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

    @classmethod
    def init_order(cls):
        return 1

    def webgui_contents(self):
        container = ui.column(align_items="center").classes("w-full")
        with container:
            with ui.card().classes("w-1/2 justify-center items-center"):
                ui.label("Pi Admin").classes(
                    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
                )
                ui.button(
                    "Power Off",
                    on_click=self.poweroff,
                ).classes("w-full")
                ui.button(
                    "Reboot",
                    on_click=self.reboot,
                ).classes("w-full")
                ui.button(
                    "Restart MAVProxy",
                    on_click=self.restart_mavproxy,
                ).classes("w-full")
                ui.button(
                    "Restart Manfaloty Bridge",
                    on_click=self.restart_manfaloty_bridge,
                ).classes("w-full")
                ui.button(
                    "Restart Telemetry",
                    on_click=self.restart_telemetry,
                ).classes("w-full")
                ui.button(
                    "Restart Admin",
                    on_click=self.restart_admin,
                ).classes("w-full")
        return container

    def webgui_icon_name(self):
        return "terminal"

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
