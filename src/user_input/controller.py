import glob
import json
import os
from typing import Optional, Tuple
from pprint import pformat

import jsonschema
import jsonschema.exceptions
import pygame

from event_dispatcher import EventDispatcher
from logger import system_logger

__all__ = ["Controller"]

CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "displayName": {"type": "string"},
        "pygameName": {"type": "string"},
        "buttons": {"type": "integer"},
        "axes": {"type": "integer"},
        "hats": {"type": "integer"},
        "mappings": {
            "type": "object",
            "patternProperties": {
                "^[A-Z0-9]+$": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["button", "axis", "hat", "trigger"],
                        },
                        "mapping": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 0,
                        },
                        "axis": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 0,
                        },
                    },
                    "required": ["type"],
                    "additionalProperties": True,
                }
            },
            "additionalProperties": False,
        },
    },
    "required": ["displayName", "pygameName", "buttons", "axes", "hats", "mappings"],
    "additionalProperties": False,
}


CONFIG_DIRECTORY = "assets/controller/configurations"


class Controller:
    def __init__(
        self,
        dispatcher: EventDispatcher,
        deadzone_factor: float = 2,
        joystick_roundoff: int = 1,
        joystick_multiplier: int = 100,
    ) -> None:
        """
        Initialize a new Controller instance.

        :param dispatcher: The event dispatcher for handling events.
        :type dispatcher: EventDispatcher
        :param deadzone_factor: The factor by which deadzone is multiplied (default 2).
        :type deadzone_factor: float
        :param joystick_roundoff: Rounding precision for joystick values (default 1).
        :type joystick_roundoff: int
        :param joystick_multiplier: Multiplier for scaling joystick values (default 100).
        :type joystick_multiplier: int
        """
        pygame.joystick.init()
        self.__dispatcher = dispatcher
        self.__deadzone: float = 0.5
        self.__deadzone_factor: float = deadzone_factor
        self.__joystick_roundoff: int = joystick_roundoff
        self.__joystick_multiplier: int = joystick_multiplier
        self.__joystick: Optional[pygame.joystick.JoystickType] = None

        self.__previous_hat_value: Tuple[int, int] = (0, 0)
        self.__previous_trigger_value: float = 0.0

        self.__config_library: dict[str, dict] = {}
        self.__current_config_name: Optional[str] = None

        self.__library_button_mappings: dict[frozenset, str] = {}
        self.__library_hat_mappings: dict[tuple, str] = {}
        self.__library_joystick_mappings: dict[str, tuple] = {}
        self.__library_trigger_mappings: dict[int, str] = {}

        self.__load_config_libary()

        self.__dispatcher.subscribe(
            "controller_button_down", self.__on_controller_button_down
        )

    def __on_controller_button_down(self, button: str):
        match button:
            case "M":
                self.calibrate()

    def __calc_deadzones(self) -> Optional[float]:
        """
        Calculate the deadzone for joystick axes based on the current input values.

        Retrieves axis values and computes a deadzone based on the max absolute value multiplied by the deadzone factor.

        :return: The computed deadzone value, or None if the joystick is not connected or an error occurs.
        :rtype: Optional[float]
        """
        if self.__joystick is None:
            return None

        try:
            joysticks: list[int] = []
            for joystick in self.__library_joystick_mappings.values():
                joysticks.extend(list(joystick))

            axes_values = [
                self.__joystick.get_axis(i)
                for i in range(self.__joystick.get_numaxes())
                if i in joysticks
            ]
        except Exception:
            return None

        max_axis_value = max(abs(value) for value in axes_values)
        deadzone = max_axis_value * self.__deadzone_factor

        system_logger.success(f"Controller deadzones calculated: {deadzone}")

        return deadzone

    def __process_axes(self) -> None:
        """
        Process joystick axes inputs with deadzone filtering and dispatch the values.

        Maps the filtered axis values to corresponding joystick names based on the configuration.

        :return: None
        """
        if self.__joystick is None:
            return

        filtered_axes = [
            self.__process_joystick_value(
                self.__joystick.get_axis(i),
                self.__deadzone,
            )
            for i in range(self.__joystick.get_numaxes())
        ]

        system_logger.trace(f"{filtered_axes = }")

        joystick_values = {}
        for name, axes in self.__library_joystick_mappings.items():
            system_logger.trace(f"__process_axes = {name = } {axes = }")
            joystick_values[name] = tuple(filtered_axes[axis] for axis in axes)

        self.__dispatcher.dispatch("controller_joysticks", joystick_values)
        system_logger.debug(f"Controller joysticks: {pformat(joystick_values)}")

    def __process_triggers(self) -> None:
        """
        Process trigger inputs and dispatch events when a trigger threshold is crossed.

        Checks current trigger axis values against the previous value and dispatches a button down event
        when the threshold (value > 0.5) is crossed.

        :return: None
        """
        if self.__joystick is None:
            return

        if len(self.__library_trigger_mappings) == 0:
            return

        for axis_index, trigger_name in self.__library_trigger_mappings.items():
            value = self.__joystick.get_axis(axis_index)
            system_logger.trace(f"trigger {trigger_name} value = {value}")
            if value > 0.5:
                system_logger.info(f"Controller trigger {trigger_name} pressed")
                self.__dispatcher.dispatch("controller_button_down", trigger_name)

    def __process_buttons(self) -> None:
        """
        Process joystick button press and release events and dispatch associated actions.

        Retrieves button events from pygame, maps them using library mappings and dispatches appropriate events.
        Logs an error if a button combination is not recognized.

        :return: None
        """
        if self.__joystick is None:
            return

        buttons_pressed_down = frozenset(
            {e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONDOWN])}
        )
        buttons_pressed_up = frozenset(
            {e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONUP])}
        )

        system_logger.trace(f"{len(buttons_pressed_down) = }")
        system_logger.trace(f"{len(buttons_pressed_up) = }")

        if len(buttons_pressed_down) == 0 and len(buttons_pressed_up) == 0:
            return

        button_down_mapping = self.__library_button_mappings.get(buttons_pressed_down)
        if button_down_mapping is None and len(buttons_pressed_down) > 0:
            system_logger.error(f"{buttons_pressed_down} is not mapped to anything")
            return

        button_up_mapping = self.__library_button_mappings.get(buttons_pressed_up)
        if button_up_mapping is None and len(buttons_pressed_up) > 0:
            system_logger.error(f"{buttons_pressed_up} is not mapped to anything")
            return

        self.__dispatcher.dispatch("controller_button_down", button_down_mapping)
        self.__dispatcher.dispatch("controller_button_up", button_up_mapping)
        system_logger.info(
            f"Controller buttons pressed: down -> {button_down_mapping}, up -> {button_up_mapping}"
        )

    def __process_hat(self) -> None:
        """
        Process hat (D-pad) events and dispatch corresponding controller button actions.

        Reads the hat switch state, compares with the previous state, and dispatches an event if a change is detected.
        Logs the action accordingly.

        :return: None
        """
        if self.__joystick is None:
            return
        hat_events = [
            self.__joystick.get_hat(i) for i in range(self.__joystick.get_numhats())
        ]
        hat_events = [(int(i[0]), int(i[1])) for i in hat_events]

        for direction in hat_events:
            if direction == (0, 0):
                self.__previous_hat_value = (0, 0)
                continue

            if direction == self.__previous_hat_value:
                continue

            controller_button = self.__library_hat_mappings[direction]

            self.__dispatcher.dispatch("controller_button_down", controller_button)
            system_logger.info(f"Controller hat pressed: {controller_button}")

            self.__previous_hat_value = (int(direction[0]), int(direction[1]))

    def __process_joystick_value(self, value: float, deadzone: float) -> float:
        """
        Process a joystick axis value with deadzone filtering and scaling.

        If the absolute value exceeds the deadzone, the value is rounded and scaled; otherwise,
        it is simply rounded.

        :param value: The raw joystick axis value.
        :type value: float
        :param deadzone: The threshold below which the value is ignored.
        :type deadzone: float
        :return: The processed axis value.
        :rtype: float
        """
        return (
            round(value, self.__joystick_roundoff) * self.__joystick_multiplier
            if abs(value) > deadzone
            else round(value)
        )

    def __load_config_libary(self):
        """
        Load the configuration library by reading valid configuration files.

        Iterates through valid configuration files and stores their contents in the internal configuration library.
        Logs success and debugging information.

        :return: None
        """
        configs = self.__get_valid_config()
        names = self.__get_valid_config_names()

        self.__config_library = {}
        for name, config in zip(names, configs):
            self.__config_library[name] = config

        system_logger.success("Loaded config library")
        system_logger.debug(f"Config Library: {pformat(self.__config_library)}")

    def __generate_library_mappings(self):
        """
        Generate mappings for buttons, hats, joysticks, and triggers based on the current configuration.

        Populates internal mapping dictionaries using the data defined in the configuration.
        Does nothing if no current configuration is selected.

        :raises KeyError: If the expected keys are not present in the configuration.
        :return: None
        """
        if not self.__current_config_name:
            return

        mappings: dict[str, dict] = self.__config_library[self.__current_config_name][
            "mappings"
        ]

        for name, mapping in mappings.items():
            system_logger.trace(f"mappings {name = } {mapping = }")
            if mapping["type"] == "button":
                self.__library_button_mappings[frozenset(set(mapping["mapping"]))] = (
                    name
                )

            if mapping["type"] == "hat":
                self.__library_hat_mappings[tuple(mapping["mapping"])] = name

            if mapping["type"] == "axis":
                self.__library_joystick_mappings[name] = tuple(mapping["axis"])

            if mapping["type"] == "trigger":
                self.__library_trigger_mappings[mapping["axis"][0]] = name

        system_logger.trace(f"{self.__library_button_mappings = }")
        system_logger.trace(f"{self.__library_hat_mappings = }")
        system_logger.trace(f"{self.__library_joystick_mappings = }")
        system_logger.trace(f"{self.__library_trigger_mappings = }")

    def __validate_configuration(self, config: dict) -> bool:
        """
        Validate a configuration dictionary against the predefined JSON schema.

        :param config: The configuration dictionary to validate.
        :type config: dict
        :return: True if configuration is valid; False otherwise.
        :rtype: bool
        :raises jsonschema.exceptions.ValidationError: If the configuration is invalid.
        """
        try:
            jsonschema.validate(config, CONFIG_SCHEMA)
        except jsonschema.exceptions.ValidationError as err:
            system_logger.error(
                f"Controller invalid configuration {config}; err msg: {err}"
            )
            return False
        else:
            return True

    def __get_valid_config_files(self) -> list[str]:
        """
        Scan and return a list of valid configuration file paths.

        Reads files from the configuration directory, validates each configuration,
        and returns absolute paths for valid configuration files.

        :return: List of valid configuration file paths.
        :rtype: list[str]
        :raises json.JSONDecodeError: If a file cannot be parsed as JSON.
        """

        files_path = [
            os.path.abspath(f"{CONFIG_DIRECTORY}/{x}")
            for x in os.listdir(CONFIG_DIRECTORY)
        ]

        system_logger.trace(f"{files_path = }")

        valid_config_paths = []
        for file in files_path:
            with open(file) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as err:
                    system_logger.error(f"Config decoding error; err msg: {err}")
                    continue
                else:
                    if self.__validate_configuration(data):
                        valid_config_paths.append(file)

        system_logger.debug(f"Valid config paths: {valid_config_paths}")
        return valid_config_paths

    def __get_valid_config(self) -> list[dict]:
        """
        Retrieve and parse valid configuration files.

        Iterates over valid configuration file paths, parses JSON content,
        and returns a list of configuration dictionaries.

        :return: List of valid configurations.
        :rtype: list[dict]
        """
        valid_configs = []
        for file in self.__get_valid_config_files():
            with open(file) as f:
                data = json.load(f)
                valid_configs.append(data)

        system_logger.trace(f"{valid_configs = }")
        return valid_configs

    def __get_valid_config_names(self) -> list[str]:
        """
        Retrieve the base names of valid configuration files.

        Strips directory path and file extension to return configuration names.

        :return: List of configuration names.
        :rtype: list[str]
        """
        files = self.__get_valid_config_files()
        return [os.path.basename(file).split(".")[0] for file in files]

    def max_value(self) -> float:
        """
        Calculate the maximum value adjusted by the deadzone factor.

        :return: The maximum adjusted value.
        :rtype: float
        """
        return 1 * self.__deadzone_factor

    def min_value(self) -> float:
        """
        Calculate the minimum value adjusted by the deadzone factor.

        :return: The minimum adjusted value.
        :rtype: float
        """
        return -1 * self.__deadzone_factor

    def is_connected(self) -> bool:
        """
        Check if the joystick controller is connected.

        :return: True if connected and initialized, False otherwise.
        :rtype: bool
        """
        return self.__joystick is not None and self.__joystick.get_init()

    def quit(self) -> None:
        """
        Quit the joystick instance safely if it is initialized.

        If the joystick is initialized, its quit method is called.
        """
        if self.__joystick is not None:
            self.__joystick.quit()

    def calibrate(self) -> bool:
        """
        Calibrate the controller by computing and setting the deadzone.

        :return: True if calibration succeeds, False otherwise.
        :rtype: bool
        """
        res = self.__calc_deadzones()
        if res is not None:
            self.__deadzone = res
            return True
        else:
            return False

    def set_rgb_led(self, r: int, g: int, b: int) -> bool:
        """
        Set the RGB LED color by adjusting brightness values.

        :param r: Red brightness (0-255).
        :type r: int
        :param g: Green brightness (0-255).
        :type g: int
        :param b: Blue brightness (0-255).
        :type b: int
        :raises ValueError: If any color value is not in the range 0-255.
        :raises IOError: If write permission to the LED files is not available.
        :return: True if the LED was successfully set; False if files not found.
        :rtype: bool
        """
        color = ["red", "green", "blue"]

        for c, value in zip(color, [r, g, b]):
            if not 0 <= value <= 255:
                raise ValueError(
                    f"Invalid value for {c} color. Must be between 0 and 255."
                )

            brightness_file = glob.glob(f"/sys/class/leds/input*:{c}/brightness")

            if not brightness_file:
                return False

            if not os.access(brightness_file[0], os.W_OK):
                raise IOError("No write permission to the led files")

            with open(brightness_file[0], "w") as f:
                f.write(str(value))
        return True

    def update(self) -> bool:
        """
        Update the controller status and process input events.

        If the controller is not connected, dispatches the waiting event.

        :return: True if processing was successful; False otherwise.
        :rtype: bool
        """
        self.update_connection_status()
        if not self.is_connected():
            self.__dispatcher.dispatch("controller_waiting_connection")
            return False

        try:
            self.__process_axes()
            self.__process_buttons()
            self.__process_triggers()
            self.__process_hat()
        except Exception:
            return False

        return True

    def update_connection_status(self) -> None:
        """
        Update the connection status of the joystick by processing connection events.

        When a connection or disconnection event is detected, appropriate events are dispatched and the joystick
        instance is either initialized or closed. In case an exception occurs, the method retries recursively.
        """
        try:
            for event in pygame.event.get(
                [pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED]
            ):
                if event.type == pygame.JOYDEVICEADDED:
                    pygame.joystick.init()
                    self.__joystick = pygame.joystick.Joystick(event.device_index)
                    self.__dispatcher.dispatch("controller_connected")
                    system_logger.info("Controller connected")
                    self.autoload_config()
                    self.calibrate()
                    return
                else:
                    if self.__joystick is not None:
                        self.__joystick.quit()
                    self.__dispatcher.dispatch("controller_disconnected")
                    system_logger.info("Controller disconnected")
                    return
        except Exception:
            return self.update_connection_status()

    def config_names(self) -> list[str]:
        """
        Get a list of available configuration names from the library.

        :return: List of configuration names.
        :rtype: list[str]
        """
        return list(self.__config_library.keys())

    def reload_config_library(self):
        """
        Reload the configuration library by re-reading configuration files.

        Invokes internal loading mechanism to ensure the library is up-to-date.
        """
        self.__load_config_libary()

    def autoload_config(self):
        """
        Autoload the configuration using the connected joystick's properties.

        Searches the configuration library for an exact or similar match based on
        pygame name, number of buttons, hats, and axes. Sets the current configuration
        and regenerates library mappings accordingly.

        :raises AttributeError: If required attributes are not defined.
        """
        if not self.__joystick:
            return

        pygame_name = self.__joystick.get_name()
        num_buttons = self.__joystick.get_numbuttons()
        num_hats = self.__joystick.get_numhats()
        num_axes = self.__joystick.get_numaxes()

        system_logger.debug(
            f"Detected {pygame_name}: {num_buttons} buttons, {num_hats} hats and {num_axes} axes"
        )

        config_found = False
        for name, config in self.__config_library.items():
            if (
                config["pygameName"] == pygame_name
                and config["buttons"] == num_buttons
                and config["hats"] == num_hats
                and config["axes"] == num_axes
            ):
                self.__current_config_name = name
                system_logger.info(f"Autoloaded {name} as the current configuration")
                config_found = True
                break

        if not config_found:
            system_logger.warning(
                f"{pygame_name} with {num_buttons} buttons, {num_hats} hats and {num_axes} axes is not a known controller type, using similar config"
            )
            for name, config in self.__config_library.items():
                if (
                    config["buttons"] == num_buttons
                    and config["hats"] == num_hats
                    and config["axes"] == num_axes
                ):
                    self.__current_config_name = name
                    system_logger.info(
                        f"Autoloaded similar config {name} as the current configuration"
                    )
                    break

        self.__generate_library_mappings()

    def manual_config(self, config_name: str):
        """
        Manually select a configuration by name and update mappings.

        :param config_name: The configuration name to set as current.
        :type config_name: str
        """
        self.__current_config_name = config_name
        self.__generate_library_mappings()
