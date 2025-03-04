import glob
import json
import os
from typing import Optional, Tuple

import jsonschema
import jsonschema.exceptions
import pygame

from events import EventDispatcher
from logger import logging

__exports__ = ["Controller"]

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

    def max_value(self) -> float:
        """
        Calculate the maximum value adjusted by the deadzone factor.

        :return: The maximum value adjusted by the deadzone factor.
        :rtype: float
        """
        return 1 * self.__deadzone_factor

    def min_value(self) -> float:
        """
        Calculate the minimum value adjusted by the deadzone factor.

        :return: The minimum value as a float, which is the negative of the deadzone factor.
        :rtype: float
        """
        return -1 * self.__deadzone_factor

    def is_connected(self) -> bool:
        """
        Check if the joystick is connected.

        :return: True if the joystick is connected and initialized, False otherwise.
        :rtype: bool
        """
        return self.__joystick is not None and self.__joystick.get_init()

    def quit(self) -> None:
        """
        Safely quits the joystick instance if it is initialized.

        This method checks if the joystick instance (`self.__joystick`) is not `None`.
        If it is initialized, it calls the `quit` method on the joystick instance to 
        safely terminate its operation.
        """
        if self.__joystick is not None:
            self.__joystick.quit()

    def calibrate(self) -> bool:
        """
        Calibrates the controller by calculating and setting the deadzones.

        This method calls the private method `__calc_deadzones` to compute the deadzones.
        If the computation is successful (i.e., the result is not None), it sets the 
        `__deadzone` attribute to the computed value and returns True. Otherwise, it 
        returns False.

        :returns: True if calibration is successful, False otherwise.
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
        Set the RGB LED to the specified color values.

        This method sets the brightness of the red, green, and blue components of an RGB LED.
        The brightness values must be between 0 and 255 inclusive.

        :param r: Brightness value for the red component (0-255).
        :type r: int
        :param g: Brightness value for the green component (0-255).
        :type g: int
        :param b: Brightness value for the blue component (0-255).
        :type b: int
        :raises ValueError: If any of the color values are outside the range 0-255.
        :raises IOError: If there is no write permission to the LED files.
        :return: True if the LED was successfully set, False if the LED files were not found.
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
        Update the controller status and process inputs.

        This method updates the connection status of the controller. If the controller
        is not connected, it dispatches a "controller_waiting_connection" event and returns False.
        If the controller is connected, it processes the axes, buttons, triggers, and hat inputs.
        If any exception occurs during the processing, it returns False.

        :return: True if the controller is connected and inputs are processed successfully, False otherwise.
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
        Monitors and updates the connection status of the joystick controller.

        This method listens for joystick connection and disconnection events using
        the pygame library. When a joystick is connected, it initializes the joystick,
        dispatches a "controller_connected" event, logs the connection, autoloads the
        configuration, and calibrates the joystick. When a joystick is disconnected,
        it quits the joystick, dispatches a "controller_disconnected" event, and logs
        the disconnection.

        If an exception occurs during the process, the method recursively calls itself
        to retry the connection status update.

        :raises: Any exception encountered during the process will trigger a recursive
                 call to this method.
        """
        try:
            for event in pygame.event.get(
                [pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED]
            ):
                if event.type == pygame.JOYDEVICEADDED:
                    pygame.joystick.init()
                    self.__joystick = pygame.joystick.Joystick(event.device_index)
                    self.__dispatcher.dispatch("controller_connected")
                    logging.logger.info("Controller connected")
                    self.autoload_config()
                    self.calibrate()
                    return
                else:
                    if self.__joystick is not None:
                        self.__joystick.quit()
                    self.__dispatcher.dispatch("controller_disconnected")
                    logging.logger.info("Controller disconnected")
                    return
        except Exception:
            return self.update_connection_status()

    def __calc_deadzones(self) -> Optional[float]:
        """
        Calculate the deadzones for the joystick axes.

        This method calculates the deadzones for the joystick axes based on the
        joystick input values and a predefined deadzone factor. If the joystick
        is not connected or an error occurs during the calculation, it returns
        None.

        Returns:
            Optional[float]: The calculated deadzone value or None if the joystick
            is not connected or an error occurs.
        """
        if self.__joystick is None:
            return None

        try:
            joysticks: list[int] = []
            for joystick in self.__library_joystick_mappings.values():
                print(joystick)
                joysticks.extend(list(joystick))

            print(f"{joysticks = }")

            axes_values = [
                self.__joystick.get_axis(i)
                for i in range(self.__joystick.get_numaxes())
                if i in joysticks
            ]
        except Exception:
            return None

        max_axis_value = max(abs(value) for value in axes_values)
        deadzone = max_axis_value * self.__deadzone_factor

        logging.logger.success(f"Controller deadzones calculated: {deadzone}")

        return deadzone

    def __process_axes(self) -> None:
        """
        Process the joystick axes values, apply deadzone filtering, and dispatch the processed values.

        This method retrieves the current axes values from the joystick, applies a deadzone filter to each value,
        maps the filtered values to their corresponding joystick names as defined in the library joystick mappings,
        and dispatches the processed joystick values using the dispatcher.

        Returns:
            None
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

        joystick_values = {}
        for name, axes in self.__library_joystick_mappings.items():
            joystick_values[name] = tuple(filtered_axes[axis] for axis in axes)

        self.__dispatcher.dispatch("controller_joysticks", joystick_values)

    def __process_triggers(self) -> None:
        """
        Process joystick trigger inputs and dispatch events when triggers are pressed.

        This method checks the current state of joystick triggers and compares it with
        the previous state to detect trigger presses. If a trigger is pressed (i.e., its
        value crosses the threshold of 0.5 from below), it dispatches a "controller_button_down"
        event with the trigger name.

        Returns:
            None
        """
        if self.__joystick is None:
            return

        if len(self.__library_trigger_mappings) == 0:
            return

        for axis_index, trigger_name in self.__library_trigger_mappings.items():
            value = self.__joystick.get_axis(axis_index)
            if value > 0.5 and self.__previous_trigger_value <= 0.5:
                self.__dispatcher.dispatch("controller_button_down", trigger_name)
                logging.logger.info(f"Controller trigger {trigger_name} pressed")

            self.__previous_trigger_value = value

    def __process_buttons(self) -> None:
        """
        Process joystick button events and dispatch corresponding actions.

        This method checks for joystick button press and release events using the
        `pygame` library. It maps the pressed and released buttons to their
        corresponding actions using `__library_button_mappings` and dispatches
        these actions via the `__dispatcher`.

        If no buttons are pressed or released, the method returns immediately.
        If a button press or release event is not mapped to any action, an error
        is logged.

        Returns:
            None
        """
        if self.__joystick is None:
            return

        buttons_pressed_down = frozenset(
            {e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONDOWN])}
        )
        buttons_pressed_up = frozenset(
            {e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONUP])}
        )

        if len(buttons_pressed_down) == 0 and len(buttons_pressed_up) == 0:
            return

        button_down_mapping = self.__library_button_mappings.get(buttons_pressed_down)
        if button_down_mapping is None:
            logging.logger.error(f"{buttons_pressed_down} is not mapped to anything")
            return

        button_up_mapping = self.__library_button_mappings.get(buttons_pressed_up)
        if button_down_mapping is None:
            logging.logger.error(f"{buttons_pressed_up} is not mapped to anything")
            return

        self.__dispatcher.dispatch("controller_button_down", button_down_mapping)
        self.__dispatcher.dispatch("controller_button_up", button_up_mapping)
        logging.logger.info(
            f"Controller buttons pressed: down -> {button_down_mapping}, up -> {button_up_mapping}"
        )

    def __process_hat(self) -> None:
        """
        Process the hat (D-pad) events from the joystick and dispatch corresponding controller button events.

        This method reads the current state of the hat switches on the joystick, compares it with the previous state,
        and dispatches an event if there is a change. It also logs the hat press events.

        Returns:
            None
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
            print(self.__library_hat_mappings)

            self.__dispatcher.dispatch("controller_button", controller_button)
            logging.logger.info(f"Controller hat pressed: {controller_button}")

            self.__previous_hat_value = (int(direction[0]), int(direction[1]))

    def __process_joystick_value(self, value: float, deadzone: float) -> float:
        """
        Process the joystick value by applying a deadzone and scaling.

        This method processes the input joystick value by first checking if it exceeds
        a specified deadzone. If the absolute value of the input exceeds the deadzone,
        the value is rounded to a specified precision and then multiplied by a joystick
        multiplier. If the value does not exceed the deadzone, it is simply rounded.

        :param value: The input joystick value to be processed.
        :type value: float
        :param deadzone: The deadzone threshold below which the joystick value is considered negligible.
        :type deadzone: float
        :return: The processed joystick value.
        :rtype: float
        """
        return (
            round(value, self.__joystick_roundoff) * self.__joystick_multiplier
            if abs(value) > deadzone
            else round(value)
        )

    def __load_config_libary(self):
        """
        Load the configuration library.

        This method retrieves valid configurations and their corresponding names,
        then stores them in the `__config_library` attribute as a dictionary where
        the keys are the configuration names and the values are the configurations.

        The method also logs the success of loading the configuration library and
        provides a debug log of the loaded configuration library.

        :return: None
        """
        configs = self.__get_valid_config()
        names = self.__get_valid_config_names()

        self.__config_library = {}
        for name, config in zip(names, configs):
            self.__config_library[name] = config

        logging.logger.success("Loaded config library")

        logging.logger.debug(f"{self.__config_library = }")

    def __generate_library_mappings(self):
        """
        Generate library mappings for buttons, hats, joysticks, and triggers.

        This method processes the current configuration's mappings and populates
        the corresponding library mappings for different control types (button, hat,
        axis, trigger). The mappings are stored in the following attributes:
        
        - `__library_button_mappings`: Maps button combinations to their names.
        - `__library_hat_mappings`: Maps hat positions to their names.
        - `__library_joystick_mappings`: Maps joystick names to their axis tuples.
        - `__library_trigger_mappings`: Maps trigger axes to their names.

        The method does nothing if `__current_config_name` is not set.

        :raises KeyError: If the configuration does not contain expected keys.
        """
        if not self.__current_config_name:
            return

        mappings: dict[str, dict] = self.__config_library[self.__current_config_name][
            "mappings"
        ]

        for name, mapping in mappings.items():
            if mapping["type"] == "button":
                self.__library_button_mappings[frozenset(set(mapping["mapping"]))] = (
                    name
                )

            if mapping["type"] == "hat":
                self.__library_hat_mappings[tuple(mapping["mapping"])] = name

            if mapping["type"] == "axis":
                self.__library_joystick_mappings[name] = tuple(mapping["axis"])

            if mapping["type"] == "trigger":
                self.__library_trigger_mappings[mapping["axis"]] = name

    def __validate_configuration(self, config: dict) -> bool:
        """
        Validate the given configuration dictionary against a predefined schema.

        :param config: The configuration dictionary to validate.
        :type config: dict
        :returns: True if the configuration is valid, False otherwise.
        :rtype: bool
        :raises jsonschema.exceptions.ValidationError: If the configuration does not match the schema.
        """
        try:
            jsonschema.validate(config, CONFIG_SCHEMA)
        except jsonschema.exceptions.ValidationError as err:
            logging.logger.error(f"Controller invalid configuration {config}; err msg: {err}")
            return False
        else:
            return True

    def __get_valid_config_files(self) -> list[str]:
        """
        Retrieve a list of valid configuration file paths.

        This method scans the CONFIG_DIRECTORY for configuration files, attempts to load
        and validate each file, and returns a list of paths to the valid configuration files.

        Returns:
            list[str]: A list of absolute paths to valid configuration files.

        Raises:
            json.JSONDecodeError: If a file cannot be decoded as JSON.
        
        Logs:
            Logs an error message if a file cannot be decoded as JSON.
        """
        files_path = [
            os.path.abspath(f"{CONFIG_DIRECTORY}/{x}")
            for x in os.listdir(CONFIG_DIRECTORY)
        ]

        valid_config_paths = []
        for file in files_path:
            with open(file) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as err:
                    logging.logger.error(f"Config decoding error; err msg: {err}")
                    continue
                else:
                    if self.__validate_configuration(data):
                        valid_config_paths.append(file)
        return valid_config_paths

    def __get_valid_config(self) -> list[dict]:
        """
        Retrieve and parse valid configuration files.

        This method iterates over a list of valid configuration file paths,
        opens each file, parses the JSON content, and appends the resulting
        dictionary to a list. The list of dictionaries is then returned.

        :return: A list of dictionaries containing the parsed JSON data from valid configuration files.
        :rtype: list[dict]
        """
        valid_configs = []
        for file in self.__get_valid_config_files():
            with open(file) as f:
                data = json.load(f)
                valid_configs.append(data)
        return valid_configs

    def __get_valid_config_names(self) -> list[str]:
        """
        Retrieve a list of valid configuration names.

        This method fetches the valid configuration files and extracts their base names
        (i.e., the file names without the directory path and file extension).

        :return: A list of valid configuration names.
        :rtype: list[str]
        """
        files = self.__get_valid_config_files()

        return [os.path.basename(file).split(".")[0] for file in files]

    def config_names(self) -> list[str]:
        """
        Retrieve the list of configuration names.

        This method returns a list of all the keys present in the 
        configuration library.

        :return: A list of configuration names.
        :rtype: list[str]
        """
        return list(self.__config_library.keys())

    def reload_config_library(self):
        """
        Reloads the configuration library.

        This method calls the private method `__load_config_libary` to reload
        the configuration settings from the library. It ensures that the 
        latest configuration settings are loaded and applied.
        """
        self.__load_config_libary()

    def autoload_config(self):
        """
        Autoloads the joystick configuration based on the connected joystick's properties.

        This method checks if a joystick is connected and attempts to find a matching configuration
        from the configuration library based on the joystick's name, number of buttons, hats, and axes.
        If an exact match is found, it sets the current configuration to the matched configuration.
        If no exact match is found, it attempts to find a similar configuration based on the number
        of buttons, hats, and axes.

        If no similar configuration is found, it logs a warning message.

        :raises AttributeError: If `self.__joystick` or `self.__config_library` is not defined.
        """
        if not self.__joystick:
            return

        pygame_name = self.__joystick.get_name()
        num_buttons = self.__joystick.get_numbuttons()
        num_hats = self.__joystick.get_numhats()
        num_axes = self.__joystick.get_numaxes()

        config_found = False
        for name, config in self.__config_library.items():
            if (
                config["pygameName"] == pygame_name
                and config["buttons"] == num_buttons
                and config["hats"] == num_hats
                and config["axes"] == num_axes
            ):
                self.__current_config_name = name
                logging.logger.info(f"Autoloaded {name} as the current configuration")
                config_found = True
                break

        if not config_found:
            logging.logger.warning(
                f"{pygame_name} with {num_buttons} buttons, {num_hats} hats and {num_axes} axes is not a known controller type, using similar config"
            )
            for name, config in self.__config_library.items():
                if (
                    config["buttons"] == num_buttons
                    and config["hats"] == num_hats
                    and config["axes"] == num_axes
                ):
                    self.__current_config_name = name
                    logging.logger.info(
                        f"Autoloaded similar config {name} as the current configuration"
                    )
                    break

        self.__generate_library_mappings()

    def manual_config(self, config_name: str):
        """
        Manually sets the current configuration by name and generates the corresponding library mappings.

        :param config_name: The name of the configuration to set.
        :type config_name: str
        """
        self.__current_config_name = config_name
        self.__generate_library_mappings()
