import glob
import os
from typing import Optional
import pygame

from events import EventDispatcher, Event

__exports__ = ["Controller"]

LEFT_X_AXIS_INDX = 0
LEFT_Y_AXIS_INDX = 1
RIGHT_X_AXIS_INDX = 3
RIGHT_Y_AXIS_INDX = 4

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
        - `controller_left_joystick`: Dispatched with a tuple of (x, y) values.
        - `controller_right_joystick`: Dispatched with a tuple of (z, w) values.
        - `controller_button`: Dispatched when button is pressed, with the button index.
        - `controller_hat`: Dispatched when hat button is pressed, with the hat direction as tuple.
    """
    HAT_UP = (0, 1)
    HAT_DOWN = (0, -1)
    HAT_LEFT = (-1, 0)
    HAT_RIGHT = (1, 0)

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
            - "controller_left_joystick": When the left joystick is moved.
            - "controller_right_joystick": When the right joystick is moved.
            - "controller_button": When a button is pressed.
            - "controller_hat": When the hat is moved.

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
                    self.calibrate()
                    self.__dispatcher.dispatch("controller_connected")
                    return
                else:
                    if self.__joystick is not None:
                        self.__joystick.quit()
                    self.__dispatcher.dispatch("controller_disconnected")
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
            axes_values = [
                self.__joystick.get_axis(i)
                for i in range(self.__joystick.get_numaxes())
                if i
                in [
                    LEFT_X_AXIS_INDX,
                    LEFT_Y_AXIS_INDX,
                    RIGHT_X_AXIS_INDX,
                    RIGHT_Y_AXIS_INDX,
                ]
            ]
        except Exception:
            return None

        max_axis_value = max(abs(value) for value in axes_values)
        deadzone = max_axis_value * self.__deadzone_factor

        return deadzone

    def __process_axes(self) -> None:
        """
        Processes the joystick axes values, applies deadzone filtering, and dispatches events.

        This method retrieves the current axes values from the joystick, applies a deadzone filter
        to each axis value, and then maps the filtered values to specific axes (x, y, z, w). It
        dispatches two events:
        - "controller_left_joystick" with a tuple of (x, y) values.
        - "controller_right_joystick" with a tuple of (z, w) values.

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

        x, y, z, w = (0.0, 0.0, 0.0, 0.0)
        for i, j in enumerate(filtered_axes):
            if i == 0:
                x = j
            elif i == 1:
                y = j
            elif i == 3:
                z = j
            elif i == 4:
                w = j

        self.__dispatcher.dispatch("controller_left_joystick", (x, y))
        self.__dispatcher.dispatch("controller_right_joystick", (z, w))

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
        button_events = [
            self.__joystick.get_button(i)
            for i in range(self.__joystick.get_numbuttons())
        ]

        for i, button_pressed in enumerate(button_events):
            if button_pressed:
                self.__dispatcher.dispatch("controller_button", i)

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

        for direction in hat_events:
            hat_direction = (int(direction[0]), int(direction[1]))
            if hat_direction == (0, 0):
                continue
            
            self.__dispatcher.dispatch(
                Event("controller_hat", hat_direction)
            )

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
