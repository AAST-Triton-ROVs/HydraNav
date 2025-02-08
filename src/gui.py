from typing import Optional, Tuple
import pygame
from events import EventDispatcher
from logger import Logging

# armed or disarmed
# max gain
# current thottle
# current pitch
# current roll
# current yaw
# pi cpu usage
# pi memory usage
# pi temperature
# pi voltage
# pi current
# joystick


class GUI:
    TEXT_POSITION_CENTER = (-1, -1)

    def __init__(
        self,
        title: str,
        dispatcher: EventDispatcher,
        logger: Logging,
        clock: pygame.time.Clock,
        assets_dir: Optional[str] = None,
        dark_mode: bool = False,
        joystick_range_min: float = -100.0,
        joystick_range_max: float = 100.0,
    ):
        self.__title = title

        pygame.display.set_caption(self.__title)
        icon = pygame.image.load("assets/icon.png")
        pygame.display.set_icon(icon)

        self.__screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.__dark_mode = dark_mode

        self.__joystick_range_min = joystick_range_min
        self.__joystick_range_max = joystick_range_max

        self.__dispatcher = dispatcher
        self.__clock = clock
        self.__logging = logger

        self.__assets_dir = assets_dir or "assets"
        self.__light_background_image = pygame.image.load(
            f"{self.__assets_dir}/light/background.png"
        )
        self.__light_background_image = pygame.transform.scale(
            self.__light_background_image, self.__display_size()
        )
        self.__dark_background_image = pygame.image.load(
            f"{self.__assets_dir}/dark/background.png"
        )
        self.__dark_background_image = pygame.transform.scale(
            self.__dark_background_image, self.__display_size()
        )
        self.__regular_font = f"{self.__assets_dir}/regular.ttf"
        self.__mono_font = f"{self.__assets_dir}/monospace.ttf"

        joystick_width = 125
        display_size = self.__display_size()
        self.__logging.logger.info(f"GUI display size: {display_size}")
        self.__dispatcher.subscribe(
            "controller_left_joystick",
            lambda data: self.draw_joystick_circle(
                (joystick_width, display_size[1] - joystick_width),
                joystick_width,
                data[0],
                data[1],
                dot_size=20,
            ),
        )
        self.__dispatcher.subscribe(
            "controller_disconnected",
            lambda _: self.remove_joystick_circle(
                (joystick_width, display_size[1] - joystick_width), joystick_width, 20
            ),
        )

        self.__dispatcher.subscribe(
            "controller_right_joystick",
            lambda data: self.draw_joystick_circle(
                (display_size[0] - joystick_width, display_size[1] - joystick_width),
                joystick_width,
                data[0],
                data[1],
                dot_size=20,
            ),
        )
        self.__dispatcher.subscribe(
            "controller_disconnected",
            lambda _: self.remove_joystick_circle(
                (display_size[0] - joystick_width, display_size[1] - joystick_width),
                joystick_width,
                20,
            ),
        )

        self.__dispatcher.subscribe(
            "controller_waiting_connection",
            lambda _: self.render_text(
                "Controller Disconnected",
                50,
                self.TEXT_POSITION_CENTER,
                (255, 0, 0),
                (0, 0, 0),
            ),
        )

        self.__dispatcher.subscribe(
            "controller_connected",
            lambda _: self.remove_text(
                "Controller Disconnected",
                50,
                self.TEXT_POSITION_CENTER,
            ),
        )

        self.__dispatcher.subscribe(
            "notifier_volume_change",
            lambda data: self.render_text(
                f"Volume: {str(data) + '%':<5}",
                20,
                (80, 0),
                (0, 0, 0),
            ),
        )

        self.__dispatcher.subscribe(
            "telemetery",
            lambda data: self.render_text(
                f"{(
                    f"| CPU {str(data.cpu_usage) + '%':^10} | CPU TEMP {str(data.cpu_temp) + '°C':^10} | "
                    f"RAM {str(data.ram_usage) + '%':^10} | DISK {str(data.disk_usage) + '%':^10} | "
                    f"NETWORK {str(data.network_usage[0]) + 'B/s':^10} {str(data.network_usage[1]) + 'B/s':^10} | GPU {str(data.gpu_usage) + '%':^10} | "
                    f"GPU TEMP {str(data.gpu_temp) + '°C':^10} |"
                ):<160}",
                20,
                (220, 0),
                (0, 0, 0),
            ),
        )
        self.__set_theme("light")

    def __calc_relative_size(self, size: int) -> int:
        return int(size * (self.__display_size()[1] / 1080))

    def __clear_rect(self, rect: pygame.Rect):
        self.__screen.blit(self.__background_image, rect, rect)

    def __display_size(self) -> Tuple[int, int]:
        return pygame.display.get_surface().get_size()

    def __invert_rgb(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return (abs(color[0] - 255), abs(color[1] - 255), abs(color[2] - 255))

    def __map_joystick_to_range(
        self, value: float, out_min: float, out_max: float
    ) -> float:
        return (value - self.__joystick_range_min) * (out_max - out_min) / (
            self.__joystick_range_max - self.__joystick_range_min
        ) + out_min

    def __process_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        if self.__dark_mode:
            return self.__invert_rgb(color)

        return color

    def __set_theme(self, theme: str):
        if theme == "dark":
            self.__background_image = self.__dark_background_image
        else:
            self.__background_image = self.__light_background_image

        self.clear_screen()

    def clear_screen(self):
        self.__screen.blit(self.__background_image, (0, 0))
        pygame.display.update(self.__background_image.get_rect())

        self.__dispatcher.dispatch("gui_screen_cleared")
        self.__logging.logger.info("GUI screen cleared")

    def draw_joystick_circle(
        self,
        center: tuple[int, int],
        radius: int,
        y: float,
        x: float,
        border_width: int = 5,
        dot_size: int = 10,
    ):
        radius = self.__calc_relative_size(radius)
        dot_size = self.__calc_relative_size(dot_size)

        top_left = (center[0] - radius - dot_size, center[1] - radius)
        bounding_rect = pygame.Rect(top_left, (2.5 * radius, 2.5 * radius))

        self.__clear_rect(bounding_rect)

        circ_color = self.__process_color((0, 0, 0))
        dot_color = self.__process_color((255, 0, 0))

        dot_x = int(center[0] + self.__map_joystick_to_range(y, -radius, radius))
        dot_y = int(center[1] + self.__map_joystick_to_range(x, -radius, radius))

        pygame.draw.circle(
            self.__screen,
            circ_color,
            center,
            radius,
            self.__calc_relative_size(border_width),
        )
        pygame.draw.circle(
            self.__screen,
            dot_color,
            (self.__calc_relative_size(dot_x), self.__calc_relative_size(dot_y)),
            self.__calc_relative_size(dot_size),
        )

        pygame.display.update(bounding_rect)

    def remove_joystick_circle(
        self, center: tuple[int, int], radius: int, dot_size: int
    ):
        radius = self.__calc_relative_size(radius)

        top_left = (
            self.__calc_relative_size(
                center[0] - radius - self.__calc_relative_size(dot_size)
            ),
            self.__calc_relative_size(center[1] - radius),
        )
        bounding_rect = pygame.Rect(top_left, (2.5 * radius, 2.5 * radius))

        self.__clear_rect(bounding_rect)

        pygame.display.update(bounding_rect)

    def remove_text(
        self,
        text: str,
        size: int,
        position: tuple[int, int],
    ):
        font = pygame.font.Font(self.__regular_font, self.__calc_relative_size(size))
        rendered_text = font.render(text, True, (0, 0, 0))
        text_rect = rendered_text.get_rect()

        if position == self.TEXT_POSITION_CENTER:
            display_size = self.__display_size()
            position = (
                display_size[0] // 2 - text_rect.width // 2,
                display_size[1] // 2 - text_rect.height // 2,
            )
        else:
            position = (
                self.__calc_relative_size(position[0]),
                self.__calc_relative_size(position[1]),
            )

        text_rect.topleft = position
        # 'clear' the screen by placing a part of the background image over the old text,
        self.__clear_rect(text_rect)

        pygame.display.update(text_rect)

    def render_logging(self, position: tuple[int, int]):
        bounding_rect = pygame.Rect(
            position,
            (
                position[0] + self.__calc_relative_size(500),
                position[1] + self.__calc_relative_size(500),
            ),
        )
        self.__clear_rect(bounding_rect)

        position = (
            self.__calc_relative_size(position[0]),
            self.__calc_relative_size(position[1]),
        )
        y_offset = position[1]
        font = pygame.font.Font(self.__mono_font, self.__calc_relative_size(10))
        for msg in self.__logging.get_messages():
            text_surface = font.render(msg, True, self.__process_color((0, 0, 0)))
            self.__screen.blit(text_surface, (position[0], y_offset))
            y_offset += self.__calc_relative_size(10)

        pygame.display.update(bounding_rect)

    def render_text(
        self,
        text: str,
        size: int,
        position: tuple[int, int],
        color: tuple[int, int, int],
        bg_color: Optional[tuple[int, int, int]] = None,
    ):
        font = pygame.font.Font(self.__regular_font, self.__calc_relative_size(size))
        if bg_color:
            rendered_text = font.render(
                text, True, self.__process_color(color), self.__process_color(bg_color)
            )
        else:
            rendered_text = font.render(text, True, self.__process_color(color))
        text_rect = rendered_text.get_rect()

        position = (
            self.__calc_relative_size(position[0]),
            self.__calc_relative_size(position[1]),
        )

        if position == self.TEXT_POSITION_CENTER:
            display_size = self.__display_size()
            position = (
                display_size[0] // 2 - text_rect.width // 2,
                display_size[1] // 2 - text_rect.height // 2,
            )

        text_rect.topleft = position
        # 'clear' the screen by placing a part of the background image over the old text,
        # before blitting the new text
        self.__clear_rect(text_rect)

        self.__screen.blit(rendered_text, position)
        pygame.display.update(text_rect)

    def toggle_theme(self):
        self.__dark_mode = not self.__dark_mode
        if self.__dark_mode:
            self.__set_theme("dark")
            self.__logging.logger.info("GUI theme set to dark")
        else:
            self.__set_theme("light")
            self.__logging.logger.info("GUI theme set to light")

    def update(self):
        self.render_text(
            f"FPS: {round(self.__clock.get_fps())}",
            self.__calc_relative_size(20),
            (0, 0),
            (0, 0, 0),
        )
        self.render_logging((0, 20))

        for event in pygame.event.get([pygame.KEYDOWN]):
            self.__dispatcher.dispatch("gui_key", event.key)
            self.__logging.logger.info(
                f"GUI key <{pygame.key.name(event.key)}> pressed"
            )
