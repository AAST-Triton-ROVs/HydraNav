import multiprocessing
import queue
import random
import time
from hydranav.core.has_webgui import HasWebGUI
from hydranav.manfaloty.daemon import ManfalotyDaemon
from hydranav.manfaloty.enums import ManfalotyCommands
from hydranav.core import request_manager, event_dispatcher, GCSModule, TTS
from nicegui import ui
import threading

PUMP_ON_LINE = TTS.register_line("Pump On")
PUMP_OFF_LINE = TTS.register_line("Pump OFF")
MORSE_LETTERS = {
    "a": ".-",
    "b": "-...",
    "c": "-.-.",
    "d": "-..",
    "e": ".",
    "f": "..-.",
    "g": "--.",
    "h": "....",
    "i": "..",
    "j": ".---",
    "k": "-.-",
    "l": ".-..",
    "m": "--",
    "n": "-.",
    "o": "---",
    "p": ".--.",
    "q": "--.-",
    "r": ".-.",
    "s": "...",
    "t": "-",
    "u": "..-",
    "v": "...-",
    "w": ".--",
    "x": "-..-",
    "y": "-.--",
    "z": "--..",
}
MORSE_CODE_DOT_TIME_S = 1


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

        self.__webgui_morse_code_text_box: ui.input | None = None
        self.__webgui_ph_reading_label: ui.label | None = None

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
        event_dispatcher.subscribe("mapper/PUMP_ON", lambda _: self.relay_on())
        event_dispatcher.subscribe("mapper/PUMP_OFF", lambda _: self.relay_off())
        event_dispatcher.subscribe(
            "mapper/PH_TAKE_READING",
            lambda _: self.take_ph_reading(),
        )

        request_manager.register_handler("manfaloty/restart", self.restart_arduino)
        request_manager.register_handler("manfaloty/reset", self.reset_motors)
        request_manager.register_handler("manfaloty/start-pump", self.pump_on)
        request_manager.register_handler("manfaloty/stop-pump", self.pump_off)

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
                    ui.label("Pump").classes("w-1/4 text-center")
                    ui.button(
                        "On",
                        on_click=self.pump_on,
                    ).classes("w-1/3")
                    ui.button(
                        "Off",
                        on_click=self.pump_off,
                    ).classes("w-1/3")
                with ui.row().classes("w-full justify-center"):
                    self.__webgui_ph_reading_label = ui.label("VOID").classes(
                        "w-1/2 text-center font-bold bg-blue-500 text-white text-xl h-12 flex items-center justify-center"
                    )
                    ui.button(
                        "Take PH Reading",
                        on_click=self.take_ph_reading,
                    ).classes("w-1/3")
                with ui.row().classes("w-full justify-center"):
                    self.__webgui_morse_code_text_box = ui.input(
                        label="Morse Code",
                        placeholder="start typing",
                    ).classes("w-1/3")
                    ui.button(
                        "Submit",
                        on_click=self.morse_code_callback,
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

    def pump_on(self):
        event_dispatcher.dispatch("manfaloty/pump-on")
        self.relay_on()

    def pump_off(self):
        event_dispatcher.dispatch("manfaloty/pump-off")
        self.relay_off()

    def relay_on(self):
        self.__send_command(ManfalotyCommands.RELAY_ON)

    def relay_off(self):
        self.__send_command(ManfalotyCommands.RELAY_OFF)

    def take_ph_reading(self):
        if self.__webgui_ph_reading_label is None:
            return

        event_dispatcher.dispatch("manfaloty/ph-take-reading")
        self.__send_command(ManfalotyCommands.PH_TAKE_READING)

        self.__webgui_ph_reading_label.set_text("...")

    def morse_code_callback(self):
        if self.__webgui_morse_code_text_box is None:
            return

        contents: str = self.__webgui_morse_code_text_box.value
        threading.Thread(
            target=self.play_morse_code,
            args=(contents.lower().strip(),),
            daemon=True,
        ).start()

    def play_morse_code(self, text: str):
        # According to an International Telecommunication Union standard

        # A dash is equal to three dots.
        # The space between the signals forming the same letter is equal to one dot.
        # The space between two letters is equal to three dots.
        # The space between two words is equal to seven dots.

        for letter in text:
            if letter == " ":
                time.sleep(MORSE_CODE_DOT_TIME_S * 7)
                continue

            morse_letter = MORSE_LETTERS[letter]

            for char in morse_letter:
                self.relay_on()
                if char == ".":
                    time.sleep(MORSE_CODE_DOT_TIME_S)
                else:
                    time.sleep(MORSE_CODE_DOT_TIME_S * 3)

                self.relay_off()
                time.sleep(MORSE_CODE_DOT_TIME_S)

            time.sleep(MORSE_CODE_DOT_TIME_S * 3)
