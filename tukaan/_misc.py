from __future__ import annotations

from typing import NamedTuple


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
