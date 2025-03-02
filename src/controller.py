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
    """
    Controller class for handling joystick input and dispatching events.

    Attributes:
        HAT_UP (tuple): Tuple representing the upward direction of the hat switch.
        HAT_DOWN (tuple): Tuple representing the downward direction of the hat switch.
        HAT_LEFT (tuple): Tuple representing the left direction of the hat switch.
        HAT_RIGHT (tuple): Tuple representing the right direction of the hat switch.

    Events:
        - `controller_waiting_connection`: When the controller is not connected.
        - `controller_connected`: When the controller is connected.
        - `controller_disconnected`: When the controller is disconnected.
        - `controller_joysticks`: Dispatched with a tuple of (x, y, z, w) values.
        - `controller_button`: Dispatched when button is pressed, with the button index.
    """

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

        Returns:
            float: The maximum value after applying the deadzone factor.
        """
        return 1 * self.__deadzone_factor

    def min_value(self) -> float:
        """
        Calculate the minimum value considering the deadzone factor.

        Returns:
            float: The minimum value, which is the negative of the deadzone factor.
        """
        return -1 * self.__deadzone_factor

    def is_connected(self) -> bool:
        """
        Check if the joystick is connected.

        Returns:
            bool: True if the joystick is connected and initialized, False otherwise.
        """
        return self.__joystick is not None and self.__joystick.get_init()

    def quit(self) -> None:
        """
        Safely quits the joystick instance if it is initialized.

        This method checks if the joystick instance is not None and calls its
        quit method to release any resources or connections associated with it.
        """
        if self.__joystick is not None:
            self.__joystick.quit()

    def calibrate(self) -> bool:
        """
        Calibrates the controller by calculating and setting new deadzones.

        Returns:
            bool: True if recalibration was successful and deadzones were set, False otherwise.
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

        This method sets the brightness of the red, green, and blue components of an RGB LED
        by writing the specified values to the corresponding system files.

        Args:
            r (int): The brightness value for the red component (0-255).
            g (int): The brightness value for the green component (0-255).
            b (int): The brightness value for the blue component (0-255).

        Returns:
            bool: True if the operation was successful, False if the brightness file for any color was not found.

        Raises:
            ValueError: If any of the color values are not in the range 0-255.
            IOError: If there is no write permission to the LED files.
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
        Updates the controller's status and processes input events.

        This method first updates the connection status of the controller. If the controller
        is not connected, it dispatches a "controller_waiting_connection" event and returns False.
        If the controller is connected, it processes the axes, buttons, and hat inputs. If any
        exception occurs during this processing, it returns False.

        Events Dispatched:
            - "controller_waiting_connection": When the controller is not connected.
            - "controller_connected": When the controller is connected.
            - "controller_disconnected": When the controller is disconnected.
            - "controller_joysticks": When the left joystick is moved.
            - "controller_button": When a button is pressed.

        Returns:
            bool: True if the controller is connected and input events are processed successfully,
              False otherwise.
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
        Updates the connection status of the joystick controller.

        This method listens for joystick connection and disconnection events
        using pygame. When a joystick is connected or disconnected, it initializes
        or quits the joystick respectively and dispatches the corresponding events.

        Events Dispatched:
            - "controller_connected": Dispatched when a joystick is connected.
            - "controller_disconnected": Dispatched when a joystick is disconnected.

        If an exception occurs during the process, the method will recursively call
        itself to retry the update.

        Returns:
            None
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
        Calculate the deadzone value for the joystick axes.

        This method calculates the deadzone value based on the maximum absolute
        value of the joystick axes specified by their indices. The deadzone is
        determined by multiplying the maximum axis value by a predefined deadzone
        factor.

        Returns:
            Optional[float]: The calculated deadzone value, or None if the joystick
            is not initialized or an error occurs during calculation.
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
        Processes the joystick axes values, applies deadzone filtering, and dispatches events.

        This method retrieves the current axes values from the joystick, applies a deadzone filter
        to each axis value, and then maps the filtered values to specific axes (x, y, z, w). It
        dispatches two events:
        - "controller_joysticks" with a tuple of (z, w) values.

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
        Processes the button events from the joystick and dispatches corresponding events.

        This method checks the state of each button on the joystick. If a button is pressed,
        it dispatches an event with the format "controller_button_{i}", where {i} is the index
        of the button.

        Events Dispatched:
            - "controller_button": Dispatched when button is pressed, with the button index.
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
        Processes the hat (D-pad) input from the joystick and dispatches corresponding events.

        This method checks the current state of the hat switches on the joystick. For each hat direction,

        Events Dispatched:
            - Event("controller_hat"): Dispatched for hat press, with the direction as tuple

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
        Processes the joystick value by applying a deadzone and scaling.

        This method takes a joystick input value, applies a deadzone threshold to
        ignore small movements, and scales the value based on predefined
        round-off and multiplier settings.

        Args:
            value (float): The raw joystick input value.
            deadzone (float): The threshold below which the joystick input is
                              considered as zero.

        Returns:
            float: The processed joystick value after applying the deadzone and
                   scaling.
        """
        return (
            round(value, self.__joystick_roundoff) * self.__joystick_multiplier
            if abs(value) > deadzone
            else round(value)
        )

    def __load_config_libary(self):
        """
        Load the configuration library from valid configuration files.

        This method retrieves valid configuration files and their names, then
        populates the configuration library with these configurations.

        Returns:
            None
        """
        configs = self.__get_valid_config()
        names = self.__get_valid_config_names()

        self.__config_library = {}
        for name, config in zip(names, configs):
            self.__config_library[name] = config

        logging.logger.success("Loaded config library")

        logging.logger.debug(f"{self.__config_library = }")

    def __generate_library_mappings(self):
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
        Validate a configuration against the predefined schema.

        Args:
            config (dict): The configuration dictionary to validate.

        Returns:
            bool: True if the configuration is valid, False otherwise.
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
        Retrieve valid configuration file paths.

        This method checks each file in the configuration directory, validates
        its content, and returns a list of valid configuration file paths.

        Returns:
            list[str]: A list of valid configuration file paths.
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
        Retrieve valid configurations.

        This method reads and validates the content of each valid configuration
        file, and returns a list of valid configuration dictionaries.

        Returns:
            list[dict]: A list of valid configuration dictionaries.
        """
        valid_configs = []
        for file in self.__get_valid_config_files():
            with open(file) as f:
                data = json.load(f)
                valid_configs.append(data)
        return valid_configs

    def __get_valid_config_names(self) -> list[str]:
        """
        Retrieve the names of valid configuration files.

        This method extracts the names of valid configuration files by removing
        their file extensions.

        Returns:
            list[str]: A list of valid configuration file names.
        """
        files = self.__get_valid_config_files()

        return [os.path.basename(file).split(".")[0] for file in files]

    def config_names(self) -> list[str]:
        return list(self.__config_library.keys())

    def reload_config_library(self):
        """
        Reload the configuration library.

        This method reloads the configuration library by calling the
        __load_config_libary method.

        Returns:
            None
        """
        self.__load_config_libary()

    def autoload_config(self):
        """
        Automatically load the configuration for the connected joystick.

        This method checks the connected joystick's name, number of buttons, and
        number of axes, and loads the corresponding configuration from the
        configuration library. If no matching configuration is found, it loads
        the default configuration.

        Returns:
            None
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
        Manually set the configuration for the controller.

        Args:
            config_name (str): The name of the configuration to set.

        Returns:
            None
        """
        self.__current_config_name = config_name
        self.__generate_library_mappings()
