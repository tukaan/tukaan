from __future__ import annotations

from collections import namedtuple
from pathlib import Path
from tukaan._system import Platform
from tukaan.exceptions import PlatformSpecificError

Bbox = namedtuple("Bbox", ["x", "y", "width", "height"])
Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])


class CursorFile:
    def __init__(self, source: Path):
        if Platform.os != "Windows":
            raise PlatformSpecificError(f"Cannot specify cursor from file on {Platform.os}")

        if source.suffix not in (".ani", ".cur"):
            raise ValueError(
                f'Bad file type for Windows cursor: "{source.suffix}". Should be one of ".cur" or ".ani"'
            )
        self._name = f"@{source!s}"

    @classmethod
    def __from_tcl__(cls, value: str) -> CursorFile:
        cursor = cls.__new__(cls)
        cursor._name = value
        return cursor

    def __repr__(self) -> str:
        return f"CursorFile(Path({self._name.lstrip('@')!r}))"
