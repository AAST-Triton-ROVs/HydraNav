from functools import partial
import multiprocessing.synchronize
import queue
import time
from typing import Optional

from numpy import interp
from hydranav.controller_input.controller_events import (
    AbsoluteAxisMotion,
    ButtonDown,
    ButtonHold,
    ControllerConnected,
    ControllerDisconnected,
    ControllerEvents,
)
from hydranav.core import LoggerMixin, config_manager
import multiprocessing
import pyglet

JOYSTICK_DEAD_ZONE = config_manager["controller", "joystickDeadZone"]
# JOYSTICK_ROUND_OFF = config_manager["controller", "joystickRoundOff"]
# JOYSTICK_MULTIPLIER = config_manager["controller", "joystickMultiplier"]
CONTROLLER_CONFIGS = config_manager["controller", "configs"]
TIME_UNTIL_HOLD_TRIGGERED = config_manager["controller", "timeUntilHoldTriggeredSec"]
TIME_BETWEEN_HOLD_TRIGGERS = config_manager["controller", "timeBetweenHoldTriggerSec"]
TRIGGER_PRESS_THRESHOLD = config_manager["controller", "triggerPressThreshold"]
EVENT_LOOP_TIMEOUT = 0.1
JOYSTICK_MIN = -100
JOYSTICK_MAX = 100


class ControllerDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(
        self,
        event_queue: multiprocessing.Queue,
        quit_event: multiprocessing.synchronize.Event,
    ):
        multiprocessing.Process.__init__(self, daemon=True)
        LoggerMixin.__init__(self)

        self.__event_queue: multiprocessing.Queue[ControllerEvents] = event_queue
        self.__quit_event = quit_event
        self.__controller_device: Optional[pyglet.input.Device] = None
        self.__controller_connected = False

        self.__current_config: dict = {}

        self.__button_mappings: dict[tuple[str], str] = {}
        self.__button_hold_states: dict[str, dict[str, float | bool]] = {}

        self.__hat_mappings: dict[tuple[tuple[str], int], str] = {}
        self.__hat_hold_states: dict[str, dict[str, float | bool]] = {}

        self.__axis_mappings: dict[tuple[str], str] = {}

    def __button_down_event(self, button: str):
        try:
            self.__event_queue.put_nowait(ButtonDown(button))
        except queue.Full:
            return

    def __button_hold_event(self, button: str):
        try:
            self.__event_queue.put_nowait(ButtonHold(button))
        except queue.Full:
            return

    def __absolute_axis_motion_event(self, axis: str, value: int):
        try:
            self.__event_queue.put_nowait(AbsoluteAxisMotion(axis, value))
        except queue.Full:
            return

    def __controller_connected_event(self, controller_name: str):
        try:
            self.__event_queue.put_nowait(ControllerConnected(controller_name))
        except queue.Full:
            return

    def __controller_disconnected_event(self):
        try:
            self.__event_queue.put_nowait(ControllerDisconnected())
        except queue.Full:
            return

    def __get_controller(self):
        devices = pyglet.input.get_devices()
        for config in CONTROLLER_CONFIGS:
            for device in devices:
                if device.name == config["deviceName"]:
                    # this means that this devices is supported
                    self._logger.info(f"Controller device '{device.name}' was detected")
                    self.__controller_device = device
                    self.__controller_connected = True
                    self.__controller_device.open()

                    self.__current_config = config
                    for mapping, data in config["mappings"].items():
                        match data["type"]:
                            case "button":
                                self.__button_mappings[tuple(data["names"])] = mapping
                            case "hat":
                                self.__hat_mappings[
                                    (tuple(data["names"]), data["onValue"])
                                ] = mapping
                            case "axis":
                                self.__axis_mappings[tuple(data["names"])] = mapping

                    return

    def __register_control_callbacks(self):
        if self.__controller_device is None:
            return

        for control in self.__controller_device.get_controls():
            if isinstance(control, pyglet.input.Button):
                on_press_callback = partial(self.__button_on_press_callback, control)
                on_release_callback = partial(
                    self.__button_on_release_callback,
                    control,
                )
                control.set_handler("on_press", on_press_callback)
                control.set_handler("on_release", on_release_callback)
            elif isinstance(control, pyglet.input.AbsoluteAxis):
                callback = partial(self.__absolute_axis_callback, control)
                control.set_handler("on_change", callback)
            else:
                self._logger.warning(f"{control} is not supported")

    def __absolute_axis_callback(self, axis: pyglet.input.AbsoluteAxis, value: int):
        # this callback processes joystick axes, hats, and triggers

        # process joystick axes
        self.__process_axis_joystick(axis, value)

        # process triggers
        self.__process_axis_trigger(axis, value)

        # process hats
        self.__process_axis_hat(axis, value)

    def __process_axis_joystick(
        self,
        axis: pyglet.input.AbsoluteAxis,
        value: int,
    ):
        center_point = int((axis.min + axis.max) / 2)
        for names, mapping in self.__axis_mappings.items():
            if (axis.raw_name and axis.raw_name in names) or (
                axis.name and axis.name in names
            ):
                mapped_value = int(
                    interp(
                        value,
                        [axis.min, axis.max],
                        [JOYSTICK_MIN, JOYSTICK_MAX],
                    )
                )
                if abs(value - center_point) <= JOYSTICK_DEAD_ZONE:
                    continue

                self.__absolute_axis_motion_event(mapping, mapped_value)
                self._logger.debug(
                    f"Controller axis motion '{mapping}' : {mapped_value}"
                )

    def __process_axis_trigger(self, axis: pyglet.input.AbsoluteAxis, value: int):
        # TODO: PROCESS TRIGGERS
        ...

    def __process_axis_hat(self, axis: pyglet.input.AbsoluteAxis, value: int):
        for data, mapping in self.__hat_mappings.items():
            if (axis.raw_name and axis.raw_name in data[0]) or (
                axis.name and axis.name in data[0]
            ):
                if data[1] == value:
                    self.__button_down_event(mapping)
                    self.__hat_hold_states[mapping] = {
                        "lastPressed": time.monotonic(),
                        "pressedBefore": False,
                    }
                    self._logger.debug(f"Controller hat press: {mapping}")
                elif value == 0:
                    # check if mapping is already in self.__hat_hold_states
                    if self.__hat_hold_states.get(mapping):
                        del self.__hat_hold_states[mapping]
                        self._logger.debug(f"Controller hat release: {mapping}")

    def __button_on_press_callback(self, button: pyglet.input.Button):
        for names, mapping in self.__button_mappings.items():
            if (button.raw_name and button.raw_name in names) or (
                button.name and button.name in names
            ):
                self.__button_down_event(mapping)
                self.__button_hold_states[mapping] = {
                    "lastPressed": time.monotonic(),
                    "pressedBefore": False,
                }
                self._logger.debug(f"Controller button press: {mapping}")

    def __button_on_release_callback(self, button: pyglet.input.Button):
        for names, mapping in self.__button_mappings.items():
            if (button.raw_name and button.raw_name in names) or (
                button.name and button.name in names
            ):
                if self.__button_hold_states.get(mapping):
                    del self.__button_hold_states[mapping]
                self._logger.debug(f"Controller button release: {mapping}")

    def __process_digital_hold(self):
        for mapping, data in list(self.__button_hold_states.items()) + list(
            self.__hat_hold_states.items()
        ):
            if (
                time.monotonic() - data["lastPressed"] >= TIME_UNTIL_HOLD_TRIGGERED
                and not data["pressedBefore"]
            ):
                data["pressedBefore"] = True
                data["lastPressed"] = time.monotonic()
                self.__button_hold_event(mapping)

                self._logger.debug(f"Controller digital hold: {mapping}")
            elif (
                time.monotonic() - data["lastPressed"] >= TIME_BETWEEN_HOLD_TRIGGERS
                and data["pressedBefore"]
            ):
                data["lastPressed"] = time.monotonic()
                self.__button_hold_event(mapping)

                self._logger.debug(f"Controller digital hold: {mapping}")

    def run(self):
        while not self.__quit_event.is_set():
            if self.__controller_connected:
                self.__process_digital_hold()

            # controller was never connected; connect
            if self.__controller_device is None:
                self.__get_controller()

                if self.__controller_device:
                    self.__controller_connected_event(self.__controller_device.name)
                    self.__register_control_callbacks()

            # controller was connected but now is not; reconnect
            if (
                self.__controller_connected
                and self.__controller_device is not None
                and not self.__controller_device.connected
            ):
                self._logger.info("Controller Disconnected")
                self.__controller_disconnected_event()
                self.__controller_device.close()
                self.__controller_connected = False
                self.__controller_device = None
                self.__current_config = {}
                self.__button_mappings = {}
                self.__hat_mappings = {}
                self.__axis_mappings = {}

            pyglet.app.platform_event_loop.step(EVENT_LOOP_TIMEOUT)
