import multiprocessing
import queue
from hydranav.core.has_webgui import HasWebGUI
from hydranav.manfaloty.daemon import ManfalotyDaemon
from hydranav.manfaloty.enums import ManfalotyCommands
from hydranav.core import request_manager, event_dispatcher, GCSModule, TTS
from nicegui import ui

PUMP_ON_LINE = TTS.register_line("Pump On")
PUMP_OFF_LINE = TTS.register_line("Pump OFF")


class Manfaloty(GCSModule, HasWebGUI):
    """
    Manages communication with the Manfaloty system.
    """

    def __init__(self):
        super().__init__()

        self.__command_queue: multiprocessing.Queue[ManfalotyCommands] = (
            multiprocessing.Queue(1)
        )
        self.__quit_event = multiprocessing.Event()

        self.__daemon = ManfalotyDaemon(
            self.__command_queue,
            self.__quit_event,
        )
        self.__daemon.start()

        event_dispatcher.subscribe(
            "mapper/GRIPPER_JAW_OPEN", lambda _: self.gripper_open_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_JAW_CLOSE", lambda _: self.gripper_close_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/hold/GRIPPER_JAW_OPEN", lambda _: self.gripper_open_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/hold/GRIPPER_JAW_CLOSE", lambda _: self.gripper_close_jaws()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_ROLL_LEFT", lambda _: self.gripper_roll_left()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_ROLL_RIGHT", lambda _: self.gripper_roll_right()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_PITCH_UP", lambda _: self.gripper_pitch_up()
        )
        event_dispatcher.subscribe(
            "mapper/GRIPPER_PITCH_DOWN", lambda _: self.gripper_pitch_down()
        )
        event_dispatcher.subscribe("mapper/PUMP_ON", lambda _: self.start_pump())
        event_dispatcher.subscribe("mapper/PUMP_OFF", lambda _: self.stop_pump())

        request_manager.register_handler("manfaloty/restart", self.restart_arduino)
        request_manager.register_handler("manfaloty/reset", self.reset_motors)
        request_manager.register_handler("manfaloty/start-pump", self.start_pump)
        request_manager.register_handler("manfaloty/stop-pump", self.stop_pump)

        TTS.attach_to_event(PUMP_ON_LINE, "manfaloty/pump-on")
        TTS.attach_to_event(PUMP_OFF_LINE, "manfaloty/pump-off")

    def __send_command(self, command: ManfalotyCommands):
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
                ui.label("Manfaloty").classes(
                    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
                )
                with ui.row().classes("w-full justify-center"):
                    ui.label("Gripper Jaws").classes("w-1/4 text-center")
                    ui.button(
                        "Open",
                        on_click=self.gripper_open_jaws,
                    ).classes("w-1/3")
                    ui.button(
                        "Close",
                        on_click=self.gripper_close_jaws,
                    ).classes("w-1/3")
                with ui.row().classes("w-full justify-center"):
                    ui.label("Gripper Pitch").classes("w-1/4 text-center")
                    ui.button(
                        "Up",
                        on_click=self.gripper_pitch_up,
                    ).classes("w-1/3")
                    ui.button(
                        "Down",
                        on_click=self.gripper_pitch_down,
                    ).classes("w-1/3")
                with ui.row().classes("w-full justify-center"):
                    ui.label("Gripper Roll").classes("w-1/4 text-center")
                    ui.button(
                        "Left",
                        on_click=self.gripper_roll_left,
                    ).classes("w-1/3")
                    ui.button(
                        "Right",
                        on_click=self.gripper_roll_right,
                    ).classes("w-1/3")
                with ui.row().classes("w-full justify-center"):
                    ui.label("Pump").classes("w-1/4 text-center")
                    ui.button(
                        "On",
                        on_click=self.start_pump,
                    ).classes("w-1/3")
                    ui.button(
                        "Off",
                        on_click=self.stop_pump,
                    ).classes("w-1/3")

                ui.button(
                    "Restart Arduino",
                    on_click=self.restart_arduino,
                ).classes("w-full")
                ui.button(
                    "Reset Motors",
                    on_click=self.reset_motors,
                ).classes("w-full")
        return container

    def webgui_icon_name(self):
        return "precision_manufacturing"

    def quit(self):
        self.__quit_event.set()
        self.__daemon.join()

    def status_ok(self) -> bool:
        return self.__daemon.is_alive()

    def restart_arduino(self):
        event_dispatcher.dispatch("manfaloty/arduino-restart")
        self.__send_command(ManfalotyCommands.RESTART_ARDUINO)

    def reset_motors(self):
        event_dispatcher.dispatch("manfaloty/reset-motors")
        self.__send_command(ManfalotyCommands.RESET_MOTORS)

    def gripper_open_jaws(self):
        self.__send_command(ManfalotyCommands.GRIPPER_JAW_OPEN)

    def gripper_close_jaws(self):
        self.__send_command(ManfalotyCommands.GRIPPER_JAW_CLOSE)

    def gripper_pitch_up(self):
        self.__send_command(ManfalotyCommands.GRIPPER_PITCH_UP)

    def gripper_pitch_down(self):
        self.__send_command(ManfalotyCommands.GRIPPER_PITCH_DOWN)

    def gripper_roll_left(self):
        self.__send_command(ManfalotyCommands.GRIPPER_ROLL_LEFT)

    def gripper_roll_right(self):
        self.__send_command(ManfalotyCommands.GRIPPER_ROLL_RIGHT)

    def camera_pitch_up(self):
        self.__send_command(ManfalotyCommands.CAMERA_PITCH_UP)

    def camera_pitch_down(self):
        self.__send_command(ManfalotyCommands.CAMERA_PITCH_DOWN)

    def start_pump(self):
        event_dispatcher.dispatch("manfaloty/pump-on")
        self.__send_command(ManfalotyCommands.PUMP_ON)

    def stop_pump(self):
        event_dispatcher.dispatch("manfaloty/pump-off")
        self.__send_command(ManfalotyCommands.PUMP_OFF)
