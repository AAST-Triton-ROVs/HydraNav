from queue import Queue
from typing import Tuple
from events import EventDispatcher
from logger import Logging
from rov.daemon import ROVConnectionDaemon
from rov.enums import Directions, ControlChannels
from rov.movement import Movement
from rov.command import Commands

__exports__ = ["ROV"]


class ROV:
    def __init__(
        self,
        dispatcher: EventDispatcher,
        logging: Logging,
        ip: str = "0.0.0.0",
        port: int = 2000,
    ):
        self.__movement_queue: Queue[Movement] = Queue(1)
        self.__command_queue: Queue[Commands] = Queue(1)

        self.__dispatcher = dispatcher
        self.__logging = logging
        self.__ip = ip
        self.__port = port

        self.__connection_daemon = ROVConnectionDaemon(
            self.__movement_queue,
            self.__command_queue,
            self.__ip,
            self.__port,
            self.__logging,
        )
        self.__connection_daemon.start()

        self.__dispatcher.subscribe(
            "controller_left_joystick", self.__handle_left_joystick
        )
        self.__dispatcher.subscribe(
            "controller_right_joystick", self.__handle_right_joystick
        )
        self.__dispatcher.subscribe("controller_joysticks", self.__handle_joysticks)
        self.__dispatcher.subscribe("controller_button", self.__handle_buttons)
        self.__dispatcher.subscribe("controller_hat", self.__handle_hat)

    def __handle_buttons(self, buttons: set):
        if buttons == {0}:
            self.arm()
        elif buttons == {1}:
            self.disarm()
        

    def __handle_hat(self, button: Tuple[int, int]):
        if button == (0, 1):
            self.gain_up()
        elif button == (0, -1):
            self.gain_down()

    def __handle_joysticks(self, move: Tuple[float, float, float, float]):
        x, y, z, w = move

        if x == y == z == w == 0:
            self.stop_movement()

    def __handle_left_joystick(self, move: Tuple[float, float]):
        x, y = move
        if x == y == 0:
            return

        if x > y:
            if y > 0:
                self.move_lateral_right()
            else:
                self.move_forward()
        else:
            if x > 0:  # joystick to the bottom
                self.move_backward()
            else:
                self.move_lateral_left()

    def __handle_right_joystick(self, move: Tuple[float, float]):
        x, y = move
        if x == y == 0:
            return

        if x > y:
            if x > 0:  # joystick to the left
                self.move_yaw_right()
            else:
                self.move_up()
        else:
            if y > 0:  # joystick to the bottom
                self.move_down()
            else:
                self.move_yaw_left()

    def __move(self, channel: ControlChannels, direction: Directions):
        self.__movement_queue.put(Movement(channel, direction))

    def __command(self, command: Commands):
        self.__command_queue.put(command)

    def gain_up(self):
        self.__command(Commands.GAIN_UP)
        
        self.__dispatcher.dispatch("rov_gain_up")

    def gain_down(self):
        self.__command(Commands.GAIN_DOWN)
        self.__dispatcher.dispatch("rov_gain_down")

    def arm(self):
        self.__command(Commands.ARM)
        
        self.__dispatcher.dispatch("rov_armed")

    def disarm(self):
        self.__command(Commands.DISARM)
        
        self.__dispatcher.dispatch("rov_disarmed")

    def flight_mode_manual(self):
        self.__command(Commands.SYSTEM_MODE_MANUAL)

    def flight_mode_stabilize(self):
        self.__command(Commands.SYSTEM_MODE_STABILIZE)

    def stop_movement(self):
        self.__move(ControlChannels.FORWARD, Directions.NEUTRAL)

    def move_roll_right(self):
        self.__move(ControlChannels.ROLL, Directions.POSITIVE)

    def move_roll_left(self):
        self.__move(ControlChannels.ROLL, Directions.NEGATIVE)

    def move_up(self):
        self.__move(ControlChannels.THROTTLE, Directions.POSITIVE)

    def move_down(self):
        self.__move(ControlChannels.THROTTLE, Directions.NEGATIVE)

    def move_yaw_right(self):
        self.__move(ControlChannels.YAW, Directions.POSITIVE)

    def move_yaw_left(self):
        self.__move(ControlChannels.YAW, Directions.NEGATIVE)

    def move_forward(self):
        self.__move(ControlChannels.FORWARD, Directions.POSITIVE)

    def move_backward(self):
        self.__move(ControlChannels.FORWARD, Directions.NEGATIVE)

    def move_lateral_right(self):
        self.__move(ControlChannels.LATERAL, Directions.POSITIVE)

    def move_lateral_left(self):
        self.__move(ControlChannels.LATERAL, Directions.NEGATIVE)
