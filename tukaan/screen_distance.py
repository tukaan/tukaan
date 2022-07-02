from __future__ import annotations

from dataclasses import dataclass

from ._info import Screen
from .exceptions import ColorError


def mm(amount):
    return round(amount / (Screen.ppi / 25.4), 2)


def cm(amount):
    return round(amount / (Screen.ppi / 2.54), 2)


def inch(amount):
    return round(amount / Screen.ppi, 2)


@dataclass
class ScreenDistance:
    pixels: float

    def __init__(
        self,
        px: float | None = None,
        mm: float | None = None,
        cm: float | None = None,
        inch: float | None = None,
    ) -> None:
        self._ppi = ppi = Screen.ppi

        self.pixels = 0
        if px is not None:
            self.pixels += px
        if mm is not None:
            self.pixels += mm * (ppi * 25.4)
        if cm is not None:
            self.pixels += cm * (ppi * 2.54)
        if inch is not None:
            self.pixels += inch * ppi

    def __to_tcl__(self) -> str:
        return str(self.pixels)

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> ScreenDistance:
        unit = tcl_value[-1]
        value = int(tcl_value[:-1])

        if unit == "c":
            return cls(cm=value)
        if unit == "m":
            return cls(mm=value)
        if unit == "i":
            return cls(inch=value)

        return cls(px=value)

    def __eq__(self, other: ScreenDistance):
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels == other.pixels

    def __gt__(self, other: ScreenDistance):
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels > other.pixels

    def __lt__(self, other: ScreenDistance):
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels < other.pixels

    @property
    def px(self) -> float:
        return round(self.pixels, 2)

    @property
    def mm(self) -> float:
        return mm(self.pixels)

    @property
    def cm(self) -> float:
        return cm(self.pixels)

    @property
    def inch(self) -> float:
        return inch(self.pixels)
