from enum import Enum
import pygame


class KeyboardKeys(Enum):
    Q = pygame.K_q
    W = pygame.K_w
    A = pygame.K_a
    S = pygame.K_s
    D = pygame.K_d
    E = pygame.K_e
    R = pygame.K_r
    T = pygame.K_t
    Y = pygame.K_y
    U = pygame.K_u
    I = pygame.K_i  # noqa: E741
    O = pygame.K_o  # noqa: E741
    P = pygame.K_p
    F = pygame.K_f
    G = pygame.K_g
    H = pygame.K_h
    J = pygame.K_j
    K = pygame.K_k
    L = pygame.K_l
    Z = pygame.K_z
    X = pygame.K_x
    C = pygame.K_c
    V = pygame.K_v
    B = pygame.K_b
    N = pygame.K_n
    M = pygame.K_m
    ZERO = pygame.K_0
    ONE = pygame.K_1
    TWO = pygame.K_2
    THREE = pygame.K_3
    FOUR = pygame.K_4
    FIVE = pygame.K_5
    SIX = pygame.K_6
    SEVEN = pygame.K_7
    EIGHT = pygame.K_8
    NINE = pygame.K_9
    SPACE = pygame.K_SPACE
    ESCAPE = pygame.K_ESCAPE
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT
    
    @classmethod
    def from_pygame_key(cls, key: int):
        for member in cls:
            if member.value == key:
                return member
        return None