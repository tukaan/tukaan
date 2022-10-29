from __future__ import annotations

from collections import namedtuple


class TabStop:
    def __init__(self, position: float, align: str = "left") -> None:
        if align == "decimal":
            align = "numeric"

        self.position, self.align = position, align

    def __repr__(self) -> str:
        return f"TabStop({self.position!r}, {self.align!r})"

    def __to_tcl__(self) -> tuple[float, str]:
        return self.position, self.align


Bbox = namedtuple("Bbox", ["x", "y", "width", "height"])
Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])
Version = namedtuple("Version", ["major", "minor", "patchlevel"])
