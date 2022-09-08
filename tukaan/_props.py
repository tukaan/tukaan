from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Callable

if sys.version_info >= (3, 9):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from tukaan.fonts.font import Font

from ._base import T_co, T_contra, T
from ._structures import TabStop
from ._tcl import Tcl
from ._utils import _commands, seq_pairs
from ._variables import ControlVariable
from .colors import Color
from .enums import ImagePosition, Justify, Orientation

if TYPE_CHECKING:
    from ._base import TkWidget


def config(widget: TkWidget, **kwargs) -> None:
    Tcl.call(None, widget, "configure", *Tcl.to_tcl_args(**kwargs))


def cget(widget: TkWidget, return_type: type[T], option: str) -> T:
    return Tcl.call(return_type, widget, "cget", option)


class RWProperty(Protocol[T_co, T_contra]):
    def __get__(self, instance: TkWidget, owner: object = None) -> T_co:
        ...

    def __set__(self, instance: TkWidget, value: T_contra) -> None:
        ...


class WidgetDesc(RWProperty[T, T_contra]):
    def __init__(self, command: str, type: type[T]):
        self._command = command
        self._type = type

    def __get__(self, instance: TkWidget, owner: object = None) -> T:
        if owner is None:
            return NotImplemented
        return cget(instance, self._type, f"-{self._command}")

    def __set__(self, instance: TkWidget, value: T_contra):
        config(instance, **{self._command: value})


class BoolDesc(WidgetDesc[bool, bool]):
    def __init__(self, command: str):
        super().__init__(command, bool)


class FloatDesc(WidgetDesc[float, float]):
    def __init__(self, command: str):
        super().__init__(command, float)


class Compound(WidgetDesc[ImagePosition, ImagePosition]):
    def __init__(self):
        super().__init__("compound", ImagePosition)


class TextAlign(WidgetDesc[Justify, Justify]):
    def __init__(self):
        super().__init__("justify", Justify)


class Foreground(WidgetDesc[Color, Color | str]):
    def __init__(self):
        super().__init__("foreground", Color)


class Background(WidgetDesc[Color, Color | str]):
    def __init__(self):
        super().__init__("background", Color)


class Text(WidgetDesc[str, str]):
    def __init__(self):
        super().__init__("text", str)


class Width(WidgetDesc[int, int]):
    def __init__(self):
        super().__init__("width", int)


class Height(WidgetDesc[int, int]):
    def __init__(self):
        super().__init__("height", int)


class Command(RWProperty[Callable | None, Callable | None]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return _commands.get(cget(instance, str, "-command"))

    def __set__(self, instance: TkWidget, value: Callable | None = None):
        config(instance, command=value or "")


class Orient(WidgetDesc[Orientation, Orientation]):
    def __init__(self):
        super().__init__("orient", Orientation)


class Value(WidgetDesc[int, int]):
    def __init__(self):
        super().__init__("value", int)


FontType = Font | dict[str, str | int | bool]


class FontProp(WidgetDesc[Font, FontType]):
    def __init__(self):
        super().__init__("font", Font)


class Link(RWProperty[ControlVariable, ControlVariable | None]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return cget(instance, ControlVariable, "-variable")

    def __set__(self, instance: TkWidget, value: ControlVariable | None):
        instance._variable = value
        return config(instance, variable=value or "")


class TakeFocus(WidgetDesc[bool, bool]):
    def __init__(self):
        super().__init__("takefocus", bool)


class TabStops(RWProperty[list[TabStop], TabStop | list[TabStop]]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return [TabStop(pos, align) for pos, align in seq_pairs(cget(instance, list, "-tabs"))]

    def __set__(self, instance: TkWidget, value: TabStop | list[TabStop]):
        if value is None:
            return

        if isinstance(value, TabStop):
            value = [value]

        config(instance, tabs=[y for x in value for y in x.__to_tcl__()])


PaddingType = tuple[int, int, int, int]


def _convert_padding(padding: int | tuple[int, ...] | None) -> tuple[int, ...] | str:
    if padding is None:
        return ()
    elif isinstance(padding, int):
        return (padding,) * 4
    else:
        length = len(padding)
        if length == 1:
            return padding * 4
        elif length == 2:
            return (padding[1], padding[0], padding[1], padding[0])
        elif length == 3:
            return (padding[1], padding[0], padding[1], padding[2])
        elif length == 4:
            return (padding[3], padding[0], padding[1], padding[2])
        else:
            return ""


def _convert_padding_back(padding: tuple[int, ...]) -> PaddingType:
    if len(padding) == 1:
        return (padding[0],) * 4
    elif len(padding) == 4:
        return (padding[1], padding[2], padding[3], padding[0])

    return (0,) * 4


class Padding(RWProperty[PaddingType, int | tuple[int, ...] | None]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return _convert_padding_back(cget(instance, tuple[int, ...], "-padding"))

    def __set__(self, instance: TkWidget, value: int | tuple[int, ...] | None):
        config(instance, padding=_convert_padding(value))
