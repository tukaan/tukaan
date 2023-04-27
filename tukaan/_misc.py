from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from tukaan._tcl import Tcl
from tukaan._utils import classproperty


class Bbox(NamedTuple):
    x: int
    y: int
    width: int
    height: int


class Position(NamedTuple):
    x: int
    y: int


class Size(NamedTuple):
    width: int
    height: int


class Mouse(Enum):
    LeftButton = "left"
    MiddleButton = "middle"
    RightButton = "right"
    WheelUp = "up"
    WheelDown = "down"

    @classproperty
    def x(self) -> int:
        return Tcl.eval(int, "winfo pointerx .")

    @classproperty
    def y(self) -> int:
        return Tcl.eval(int, "winfo pointery .")

    @classproperty
    def position(self) -> tuple[int]:
        return Tcl.eval((int,), "winfo pointerxy .")
