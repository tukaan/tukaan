from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from tukaan._system import Platform
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
    def __init__(self, source: Path):
        source = source.resolve().absolute()

        if Platform.os != "Windows":
            raise PlatformSpecificError(f"Cannot specify cursor from file on {Platform.os}")

        if source.suffix not in (".ani", ".cur"):
            raise ValueError(
                f'Bad file type for Windows cursor: "{source.suffix}". Should be one of ".cur" or ".ani"'
            )
        self._name = f"@{source.as_posix()!s}"

    @classmethod
    def __from_tcl__(cls, value: str) -> CursorFile:
        cursor = cls.__new__(cls)
        cursor._name = value
        return cursor

    def __repr__(self) -> str:
        return f"CursorFile(Path({self._name.lstrip('@')!r}))"
