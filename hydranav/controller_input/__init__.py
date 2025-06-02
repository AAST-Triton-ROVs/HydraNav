import multiprocessing
import queue
from hydranav.controller_input.controller_daemon import ControllerDaemon
from hydranav.controller_input.controller_events import (
    AbsoluteAxisMotion,
    ButtonDown,
    ButtonHold,
    ControllerConnected,
    ControllerDisconnected,
    ControllerEvents,
)
from hydranav.core import GCSModule, TTS, Updatable, event_dispatcher, input_mapper


CONTROLLER_CONNECTED_LINE = TTS.register_line("Controller Connected")
CONTROLLER_DISCONNECTED_LINE = TTS.register_line("Controller Disconnected")


class ControllerInput(GCSModule, Updatable):
    def __init__(self):
        super().__init__()

        self.__quit_event = multiprocessing.Event()
        self.__event_queue: multiprocessing.Queue[ControllerEvents] = (
            multiprocessing.Queue()
        )
        self.__daemon = ControllerDaemon(self.__event_queue, self.__quit_event)
        self.__daemon.start()

        TTS.attach_to_event(CONTROLLER_CONNECTED_LINE, "controller/connected")
        TTS.attach_to_event(CONTROLLER_DISCONNECTED_LINE, "controller/disconnected")

    @classmethod
    def init_order(cls):
        return 100

    def update(self):
        while not self.__event_queue.empty():
            try:
                event = self.__event_queue.get_nowait()
            except queue.Empty:
                return

            if isinstance(event, ControllerConnected):
                event_dispatcher.dispatch("controller/connected", event.device_name)
            elif isinstance(event, ControllerDisconnected):
                event_dispatcher.dispatch("controller/disconnected")
            elif isinstance(event, ButtonDown):
                input_mapper.digital_input(event.button)
            elif isinstance(event, ButtonHold):
                input_mapper.digital_input_hold(event.button)
            elif isinstance(event, AbsoluteAxisMotion):
                # TODO: CREATE INPUT MAPPER FOR ANALOGUE INPUT THAT TAKES IN AXIS NAME AND VALUE
                ...

    def quit(self):
        self.__quit_event.set()
        self.__daemon.join()

    def status_ok(self) -> bool:
        return self.__daemon.is_alive()
