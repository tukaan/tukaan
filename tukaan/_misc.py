from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from libtukaan import Xcursor

from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan.exceptions import PlatformSpecificError


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


class CursorFile:
    def __init__(self, source: Path) -> None:
        source = source.resolve().absolute()

        if Platform.os == "Windows":
            if source.suffix not in (".cur", ".ani"):
                raise ValueError(
                    f'bad cursor file type: "{source.suffix}". Should be ".cur" or ".ani"'
                )
            self._name = f"@{source.as_posix()!s}"  # Windows needs .as_posix() for some reason
        elif Tcl.windowing_system == "x11":
            self._name = Xcursor.load_cursor(source)
        else:
            raise PlatformSpecificError(f"can't load cursor from file on {Platform.os}")

    @classmethod
    def __from_tcl__(cls, value: str) -> CursorFile:
        cursor = cls.__new__(cls)
        cursor._name = value
        return cursor

    def __repr__(self) -> str:
        if "@" in self._name:
            path = self._name.lstrip("@")
        else:
            path = Xcursor.loaded_cursors[self._name]
        return f"CursorFile(Path({path!r}))"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CursorFile):
            return NotImplemented
        return self._name == other._name
