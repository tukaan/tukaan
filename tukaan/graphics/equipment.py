from __future__ import annotations

from dataclasses import dataclass

from tukaan._tcl import Tcl
from tukaan.colors import Color

from .utils import DashPattern


class Missing:
    ...


def get_missing_or_none(value):
    if value is Missing:
        return None
    elif value is None:
        return ""
    else:
        return value


@dataclass(frozen=True)
class Brush:
    fill: Color | str | None | Missing = Missing
    opacity: float = None
    fillrule: str = None

    def __to_tcl__(self) -> tuple:
        return Tcl.to_tcl_args(
            fill=get_missing_or_none(self.fill),
            fillopacity=self.opacity,
            fillrule=self.fillrule,
        )


@dataclass(frozen=True)
class Pen:
    color: Color | str | None | Missing = Missing
    width: float = None
    pattern: DashPattern = Missing
    # opacity: float = None  # causes segfaults in TkPath
    line_cap: str = None
    line_join: str = None
    # miterlimit: float = None  # buggy!

    def __to_tcl__(self) -> tuple:
        return Tcl.to_tcl_args(
            stroke=get_missing_or_none(self.color),
            strokedasharray=get_missing_or_none(self.pattern),
            strokelinecap=self.line_cap,
            strokelinejoin=self.line_join,
            # strokeopacity=self.opacity,
            strokewidth=self.width,
            # strokemiterlimit=self.miterlimit,
        )
