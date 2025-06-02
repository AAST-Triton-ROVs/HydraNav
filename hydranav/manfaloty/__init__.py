import multiprocessing
import queue
from hydranav.manfaloty.daemon import ManfalotyDaemon
from hydranav.manfaloty.enums import ManfalotyCommands
from hydranav.core import request_manager, event_dispatcher, GCSModule, TTS

PUMP_ON_LINE = TTS.register_line("Pump On")
PUMP_OFF_LINE = TTS.register_line("Pump OFF")


class Manfaloty(GCSModule):
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
