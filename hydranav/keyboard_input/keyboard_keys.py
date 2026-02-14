from enum import Enum
from typing import Optional
from pynput.keyboard import Key, KeyCode


class KeyboardKeys(Enum):
    # Function keys F1 - F12
    F1 = Key.f1
    F2 = Key.f2
    F3 = Key.f3
    F4 = Key.f4
    F5 = Key.f5
    F6 = Key.f6
    F7 = Key.f7
    F8 = Key.f8
    F9 = Key.f9
    F10 = Key.f10
    F11 = Key.f11
    F12 = Key.f12

    # Letter keys
    A_LOWER = KeyCode(char="a")
    A_UPPER = KeyCode(char="A")
    B_LOWER = KeyCode(char="b")
    B_UPPER = KeyCode(char="B")
    C_LOWER = KeyCode(char="c")
    C_UPPER = KeyCode(char="C")
    D_LOWER = KeyCode(char="d")
    D_UPPER = KeyCode(char="D")
    E_LOWER = KeyCode(char="e")
    E_UPPER = KeyCode(char="E")
    F_LOWER = KeyCode(char="f")
    F_UPPER = KeyCode(char="F")
    G_LOWER = KeyCode(char="g")
    G_UPPER = KeyCode(char="G")
    H_LOWER = KeyCode(char="h")
    H_UPPER = KeyCode(char="H")
    I_LOWER = KeyCode(char="i")
    I_UPPER = KeyCode(char="I")
    J_LOWER = KeyCode(char="j")
    J_UPPER = KeyCode(char="J")
    K_LOWER = KeyCode(char="k")
    K_UPPER = KeyCode(char="K")
    L_LOWER = KeyCode(char="l")
    L_UPPER = KeyCode(char="L")
    M_LOWER = KeyCode(char="m")
    M_UPPER = KeyCode(char="M")
    N_LOWER = KeyCode(char="n")
    N_UPPER = KeyCode(char="N")
    O_LOWER = KeyCode(char="o")
    O_UPPER = KeyCode(char="O")
    P_LOWER = KeyCode(char="p")
    P_UPPER = KeyCode(char="P")
    Q_LOWER = KeyCode(char="q")
    Q_UPPER = KeyCode(char="Q")
    R_LOWER = KeyCode(char="r")
    R_UPPER = KeyCode(char="R")
    S_LOWER = KeyCode(char="s")
    S_UPPER = KeyCode(char="S")
    T_LOWER = KeyCode(char="t")
    T_UPPER = KeyCode(char="T")
    U_LOWER = KeyCode(char="u")
    U_UPPER = KeyCode(char="U")
    V_LOWER = KeyCode(char="v")
    V_UPPER = KeyCode(char="V")
    W_LOWER = KeyCode(char="w")
    W_UPPER = KeyCode(char="W")
    X_LOWER = KeyCode(char="x")
    X_UPPER = KeyCode(char="X")
    Y_LOWER = KeyCode(char="y")
    Y_UPPER = KeyCode(char="Y")
    Z_LOWER = KeyCode(char="z")
    Z_UPPER = KeyCode(char="Z")

    # Number keys
    ZERO = KeyCode(char="0")
    ONE = KeyCode(char="1")
    TWO = KeyCode(char="2")
    THREE = KeyCode(char="3")
    FOUR = KeyCode(char="4")
    FIVE = KeyCode(char="5")
    SIX = KeyCode(char="6")
    SEVEN = KeyCode(char="7")
    EIGHT = KeyCode(char="8")
    NINE = KeyCode(char="9")

    @staticmethod
    def from_pynput(key_input) -> Optional["KeyboardKeys"]:
        """
        Convert a pynput.keyboard.Key or pynput.keyboard.KeyCode to a KeyboardKeys enum member.

        Returns:
            A matching KeyboardKeys member if one exists, otherwise None.
        """
        for member in KeyboardKeys:
            if isinstance(key_input, Key) and key_input == member.value:
                return member
            if isinstance(key_input, KeyCode):
                # Ensure both have a 'char' attribute for comparison
                if hasattr(key_input, "char") and hasattr(member.value, "char"):
                    # Compare characters (case-sensitive matching)
                    if key_input.char == member.value.char:
                        return member
        return None
