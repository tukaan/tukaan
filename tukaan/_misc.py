from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from tukaan._system import Platform
from tukaan.exceptions import PlatformSpecificError
from tukaan._tcl import Tcl
from libtukaan import Xcursor


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
            if source.suffix not in (".ani", ".cur"):
                raise ValueError(
                    f'Bad file type for Windows cursor: "{source.suffix}". Should be one of ".cur" or ".ani"'
                )
            self._name = f"@{source.as_posix()!s}"
        elif Tcl.windowing_system == "x11":
            self._name: int = Xcursor.load_cursor(source)  # TODO: int is a type error
        else:
            raise PlatformSpecificError(f"Cannot load cursor from file on {Platform.os}")

    @classmethod
    def __from_tcl__(cls, value: str) -> CursorFile:
        cursor = cls.__new__(cls)
        cursor._name = value
        return cursor

    def __repr__(self) -> str:
        return f"CursorFile(Path({self._name.lstrip('@')!r}))"
