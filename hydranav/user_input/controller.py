import time
from typing import Optional, Tuple
from pprint import pformat

import pygame

from core import event_dispatcher, system_logger, config_manager, request_manager
from user_input.input_mapper import input_mapper

__all__ = ["Controller"]

JOYSTICK_DEAD_ZONE_FACTOR = config_manager.get("controller", "joystickDeadZoneFactor")
JOYSTICK_ROUND_OFF = config_manager.get("controller", "joystickRoundOff")
JOYSTICK_MULTIPLIER = config_manager.get("controller", "joystickMultiplier")
CONTROLLER_CONFIGS = config_manager.get("controller", "configs")
TIME_UNTIL_HOLD_TRIGGERED = config_manager.get(
    "controller", "timeUntilHoldTriggeredSec"
)
TIME_BETWEEN_HOLD_TRIGGERS = config_manager.get(
    "controller", "timeBetweenHoldTriggerSec"
)
TRIGGER_PRESS_THRESHOLD = config_manager.get("controller", "triggerPressThreshold")


class Controller:
    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        self.__deadzone: float = 0.5
        self.__deadzone_factor: float = JOYSTICK_DEAD_ZONE_FACTOR
        self.__joystick_roundoff: int = JOYSTICK_ROUND_OFF
        self.__joystick_multiplier: int = JOYSTICK_MULTIPLIER
        self.__joystick: Optional[pygame.joystick.JoystickType] = None

        self.__previous_hat_value: Tuple[int, int] = (0, 0)

        self.__config_library: list[dict] = CONTROLLER_CONFIGS
        self.__current_config: Optional[dict] = None

        self.__library_button_mappings: dict[int, str] = {}
        self.__library_hat_mappings: dict[tuple, str] = {}
        self.__library_joystick_mappings: dict[str, tuple] = {}
        self.__library_trigger_mappings: dict[int, str] = {}

        self.__trigger_hold_states: dict[str, dict[str, float | bool]] = {}
        """
        ```
        {
            "<TRIGGER_NAME>" : {"time": float, "held_before": bool}
        }
        ```
        """
        self.__buttons_held: dict[str, dict[str, float | bool]] = {}
        """
        ```
        {
            "<BUTTON_NAME>" : {"time": float, "held_before": bool}
        }
        ```
        """

        request_manager.register_handler("controller/calibrate", self.calibrate)

    def __calc_deadzones(self) -> Optional[float]:
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

        event_dispatcher.dispatch("controller/joysticks", joystick_values)
        system_logger.trace(f"Controller joysticks: {pformat(joystick_values)}")

    def __process_triggers(self) -> None:
        if self.__joystick is None:
            return

        if len(self.__library_trigger_mappings) == 0:
            return

        for axis_index, trigger_name in self.__library_trigger_mappings.items():
            value = self.__joystick.get_axis(axis_index)
            system_logger.trace(f"trigger {trigger_name} value = {value}")
            if value > TRIGGER_PRESS_THRESHOLD:
                # check if trigger is in dict
                if trigger_name not in self.__trigger_hold_states.keys():
                    # trigger is not in dict
                    self.__trigger_hold_states[trigger_name] = {
                        "time": time.monotonic(),
                        "held_before": False,
                    }
                    input_mapper.button_down(trigger_name)
                else:
                    if (
                        time.monotonic()
                        - self.__trigger_hold_states[trigger_name]["time"]
                        >= TIME_UNTIL_HOLD_TRIGGERED
                        and not self.__trigger_hold_states[trigger_name]["held_before"]
                    ):
                        self.__trigger_hold_states[trigger_name] = {
                            "time": time.monotonic(),
                            "held_before": True,
                        }
                        input_mapper.button_down(trigger_name)
                    elif (
                        time.monotonic()
                        - self.__trigger_hold_states[trigger_name]["time"]
                        >= TIME_BETWEEN_HOLD_TRIGGERS
                        and self.__trigger_hold_states[trigger_name]["held_before"]
                    ):
                        input_mapper.button_down(trigger_name)
                system_logger.info(f"Controller trigger {trigger_name} pressed")

    def __process_buttons(self) -> None:
        if self.__joystick is None:
            return

        buttons_pressed_down = [
            e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONDOWN])
        ]

        buttons_pressed_up = [
            e.dict["button"] for e in pygame.event.get([pygame.JOYBUTTONUP])
        ]
        buttons_held_down = [
            i
            for i in range(self.__joystick.get_numbuttons())
            if self.__joystick.get_button(i)
        ]

        system_logger.debug(pformat(self.__buttons_held))
        for button, data in self.__buttons_held.items():
            if (
                time.monotonic() - data["time"] >= TIME_UNTIL_HOLD_TRIGGERED
                and not self.__buttons_held[button]["held_before"]
            ):
                input_mapper.button_hold(button)
                system_logger.info(f"Controller button held: {button}")
                self.__buttons_held[button]["time"] = time.monotonic()
                self.__buttons_held[button]["held_before"] = True
            elif (
                time.monotonic() - data["time"] >= TIME_BETWEEN_HOLD_TRIGGERS
                and self.__buttons_held[button]["held_before"]
            ):
                # This triggers the high frequency emit mode
                input_mapper.button_hold(button)
                system_logger.info(f"Controller button held: {button}")
                self.__buttons_held[button]["time"] = time.monotonic()

        if len(buttons_pressed_down) == 0 and len(buttons_pressed_up) == 0:
            return

        button_down_mapping = None
        if len(buttons_pressed_down) > 0:
            button_down_mapping = self.__library_button_mappings.get(
                buttons_pressed_down[0]
            )
            if button_down_mapping is None:
                system_logger.error(f"{buttons_pressed_down} is not mapped to anything")

        button_up_mapping = None
        if len(buttons_pressed_up) > 0:
            button_up_mapping = self.__library_button_mappings.get(
                buttons_pressed_up[0]
            )
            if button_up_mapping is None:
                system_logger.error(f"{buttons_pressed_up} is not mapped to anything")

        button_held_mapping = None
        if len(buttons_held_down) > 0:
            button_held_mapping = self.__library_button_mappings.get(
                buttons_held_down[0]
            )
            if button_held_mapping is None:
                system_logger.error(f"{button_held_mapping} is not mapped to anything")

        if (
            button_down_mapping is not None
            and self.__buttons_held.get(button_down_mapping) is None
        ):
            self.__buttons_held[button_down_mapping] = {
                "time": time.monotonic(),
                "held_before": False,
            }
            system_logger.debug(
                f"Adding button to hold dictionary: {button_down_mapping}"
            )

        if (
            button_up_mapping is not None
            and self.__buttons_held.get(button_up_mapping) is not None
        ):
            del self.__buttons_held[button_up_mapping]
            system_logger.debug(
                f"Removing button from hold dictionary: {button_up_mapping}"
            )

        if button_held_mapping is None and len(self.__buttons_held) > 0:
            self.__buttons_held = {}

        system_logger.info(
            f"Controller buttons pressed: down: {button_down_mapping} | up: {button_up_mapping} | held: {button_held_mapping}"
        )
        if button_down_mapping is not None:
            input_mapper.button_down(button_down_mapping)

    def __process_hat(self) -> None:
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

            input_mapper.button_down(controller_button)
            system_logger.info(f"Controller hat pressed: {controller_button}")

            self.__previous_hat_value = (int(direction[0]), int(direction[1]))

    def __process_joystick_value(self, value: float, deadzone: float) -> float:
        return (
            round(value, self.__joystick_roundoff) * self.__joystick_multiplier
            if abs(value) > deadzone
            else round(value)
        )

    def __generate_library_mappings(self):
        if not self.__current_config:
            return

        mappings: dict[str, dict] = self.__current_config["mappings"]

        for name, mapping in mappings.items():
            system_logger.trace(f"mappings {name = } {mapping = }")
            if mapping["type"] == "button":
                self.__library_button_mappings[mapping["mapping"]] = name

            if mapping["type"] == "hat":
                self.__library_hat_mappings[tuple(mapping["mapping"])] = name

            if mapping["type"] == "axis":
                self.__library_joystick_mappings[name] = tuple(mapping["axis"])

            if mapping["type"] == "trigger":
                self.__library_trigger_mappings[mapping["axis"]] = name

        system_logger.trace(f"{self.__library_button_mappings = }")
        system_logger.trace(f"{self.__library_hat_mappings = }")
        system_logger.trace(f"{self.__library_joystick_mappings = }")
        system_logger.trace(f"{self.__library_trigger_mappings = }")

    def max_value(self) -> float:
        return 1 * self.__deadzone_factor

    def min_value(self) -> float:
        return -1 * self.__deadzone_factor

    def is_connected(self) -> bool:
        return self.__joystick is not None and self.__joystick.get_init()

    def quit(self) -> None:
        if self.__joystick is not None:
            self.__joystick.quit()

    def status_ok(self) -> bool:
        return self.__joystick is not None and self.__joystick.get_init()

    def calibrate(self) -> bool:
        res = self.__calc_deadzones()
        if res is not None:
            self.__deadzone = res
            return True
        else:
            return False

    def update(self) -> bool:
        self.update_connection_status()
        if not self.is_connected():
            event_dispatcher.dispatch("controller/waiting_connection")
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
        try:
            for event in pygame.event.get(
                [pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED]
            ):
                if event.type == pygame.JOYDEVICEADDED:
                    pygame.joystick.init()
                    self.__joystick = pygame.joystick.Joystick(event.device_index)
                    event_dispatcher.dispatch("controller/connected")
                    system_logger.info("Controller connected")
                    self.autoload_config()
                    self.calibrate()
                    return
                else:
                    if self.__joystick is not None:
                        self.__joystick.quit()
                    event_dispatcher.dispatch("controller/disconnected")
                    system_logger.info("Controller disconnected")
                    return
        except Exception:
            return self.update_connection_status()

    def config_names(self) -> list[str]:
        return [config["displayName"] for config in self.__config_library]

    def autoload_config(self):
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
        for config in self.__config_library:
            if (
                config["pygameName"] == pygame_name
                and config["buttons"] == num_buttons
                and config["hats"] == num_hats
                and config["axes"] == num_axes
            ):
                self.__current_config = config
                system_logger.info(
                    f"Autoloaded {config['displayName']} as the current configuration"
                )
                config_found = True
                break

        if not config_found:
            system_logger.warning(
                f"{pygame_name} with {num_buttons} buttons, {num_hats} hats and {num_axes} axes is not a known controller type, using similar config"
            )
            for config in self.__config_library:
                if (
                    config["buttons"] == num_buttons
                    and config["hats"] == num_hats
                    and config["axes"] == num_axes
                ):
                    self.__current_config = config
                    system_logger.info(
                        f"Autoloaded similar config {config['displayName']} as the current configuration"
                    )
                    break

        self.__generate_library_mappings()

    @property
    def current_config_name(self) -> str | None:
        if self.__current_config is None:
            return None

        return self.__current_config["displayName"]

    @current_config_name.setter
    def current_config_name(self, value: str):
        if all(config.get(value) is not None for config in self.__config_library):
            raise ValueError(f"{value} is not a valid config name")

        for config in self.__config_library:
            if config["displayName"] == value:
                self.__current_config = config
                break
        self.__generate_library_mappings()
