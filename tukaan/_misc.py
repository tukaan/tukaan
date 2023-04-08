from __future__ import annotations

from enum import Enum
from typing import NamedTuple

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

    @classproperty
    def x(self):
        ...

    @classproperty
    def y(self):
        ...

    @classproperty
    def position(self):
        ...
