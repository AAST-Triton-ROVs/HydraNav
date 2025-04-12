import pygame


class CentralClock:
    def __init__(self):
        self.__clock = pygame.Clock()
        self.__time_delta: float = 0.0

    @property
    def time_delta(self) -> float:
        return self.__time_delta

    @property
    def fps(self) -> float:
        return self.__clock.get_fps()

    def tick(self, frame_rate: int):
        self.__time_delta = self.__clock.tick(frame_rate) / 1000.0


central_clock = CentralClock()
