from __future__ import annotations

from typing import Callable

intround: Callable[[float], int] = lambda x: int(round(x, 0))
round2: Callable[[float], float] = lambda x: float(round(x, 2))


class MemoryUnit:
    def __init__(self, byte_count):
        from psutil._common import bytes2human

        self.bytes = byte_count

        byte_count, unit = bytes2human(byte_count, format="%(value).2f/%(symbol)s").split("/")
        self.amount = round2(float(byte_count))

        if unit != "B":
            unit = unit + "iB"
        self.unit = unit

    def __repr__(self):
        return f"MemoryUnit({self.amount} {self.unit})"

    @property
    def B(self) -> float:
        return round2(self.bytes)

    @property
    def kiB(self) -> float:
        return round2(self.bytes / 2**10)

    @property
    def MiB(self) -> float:
        return round2(self.bytes / 2**20)

    @property
    def GiB(self) -> float:
        return round2(self.bytes / 2**30)

    @property
    def TiB(self) -> float:
        return round2(self.bytes / 2**40)

    @property
    def PiB(self) -> float:
        return round2(self.bytes / 2**50)


class ScreenDistance:
    def __init__(self, px=None, mm=None, cm=None, inch=None) -> None:
        from tukaan import Screen

        self.ppi = ppi = Screen.ppi

        self.amount = 0
        if px is not None:
            self.amount += px
        if mm is not None:
            self.amount += mm * (ppi * 25.4)
        if cm is not None:
            self.amount += cm * (ppi * 2.54)
        if inch is not None:
            self.amount += inch * ppi

    def __repr__(self) -> str:
        return f"ScreenDistance({float(self)} px)"

    def __int__(self):
        return intround(self.amount)

    def __float__(self):
        return round2(self.amount)

    def to_tcl(self) -> str:
        return str(self.amount)

    @classmethod
    def from_tcl(cls, tcl_value: str) -> ScreenDistance:
        unit = tcl_value[-1]
        value = int(tcl_value[:-1])

        if unit == "c":
            return cls(cm=value)
        if unit == "m":
            return cls(mm=value)
        if unit == "i":
            return cls(inch=value)

        return cls(px=value)

    @property
    def px(self) -> float:
        return round2(self.amount)

    @property
    def mm(self) -> float:
        return round2(self.amount / (self.ppi / 25.4))

    @property
    def cm(self) -> float:
        return round2(self.amount / (self.ppi / 2.54))

    @property
    def inch(self) -> float:
        return round2(self.amount / self.ppi)
