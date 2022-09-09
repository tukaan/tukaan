from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional, Union

if sys.version_info >= (3, 9):
    from collections.abc import Callable
    from typing import Protocol
else:
    from typing import Callable
    from typing_extensions import Protocol

from ._structures import TabStop
from ._tcl import Tcl
from ._utils import T, T_co, T_contra, _commands, seq_pairs
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


class OptionDesc(RWProperty[T, T_contra]):
    def __init__(self, option: str, type_: type[T]):
        self._option = option
        self._type = type_

    def __get__(self, instance: TkWidget, owner: object = None) -> T:
        if owner is None:
            return NotImplemented
        return cget(instance, self._type, f"-{self._option}")

    def __set__(self, instance: TkWidget, value: T_contra):
        config(instance, **{self._option: value})


class BoolDesc(OptionDesc[bool, bool]):
    def __init__(self, option: str):
        super().__init__(option, bool)


class IntDesc(OptionDesc[int, int]):
    def __init__(self, option: str):
        super().__init__(option, int)


class FloatDesc(OptionDesc[float, float]):
    def __init__(self, option: str):
        super().__init__(option, float)


class ImagePositionProp(OptionDesc[ImagePosition, ImagePosition]):
    def __init__(self):
        super().__init__("compound", ImagePosition)


class TextAlignProp(OptionDesc[Justify, Justify]):
    def __init__(self):
        super().__init__("justify", Justify)


class ForegroundProp(OptionDesc[Color, Union[Color, str]]):
    def __init__(self):
        super().__init__("foreground", Color)


class BackgroundProp(OptionDesc[Color, Union[Color, str]]):
    def __init__(self):
        super().__init__("background", Color)


class TextProp(OptionDesc[str, str]):
    def __init__(self):
        super().__init__("text", str)


class WidthProp(OptionDesc[int, int]):
    def __init__(self):
        super().__init__("width", int)


class HeightProp(OptionDesc[int, int]):
    def __init__(self):
        super().__init__("height", int)


class CommandProp(OptionDesc[Optional[Callable], Optional[Callable]]):
    def __init__(self):
        super().__init__("command", str)

    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return _commands.get(cget(instance, str, "-command"))

    def __set__(self, instance: TkWidget, value: Callable | None = None):
        super().__set__(instance, value or "")


class OrientProp(OptionDesc[Orientation, Orientation]):
    def __init__(self):
        super().__init__("orient", Orientation)


class LinkProp(RWProperty[ControlVariable, Optional[ControlVariable]]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return cget(instance, ControlVariable, "-variable")

    def __set__(self, instance: TkWidget, value: ControlVariable | None):
        instance._variable = value
        return config(instance, variable=value or "")


class FocusableProp(OptionDesc[bool, bool]):
    def __init__(self):
        super().__init__("takefocus", bool)


class TabStopsProp(RWProperty[list[TabStop], Union[TabStop, list[TabStop]]]):
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

        return ""


def _convert_padding_back(padding: tuple[int, ...]) -> PaddingType:
    if len(padding) == 1:
        return (padding[0],) * 4
    elif len(padding) == 4:
        return (padding[1], padding[2], padding[3], padding[0])

    return (0,) * 4


class PaddingProp(RWProperty[PaddingType, Union[int, tuple[int, ...], None]]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return _convert_padding_back(cget(instance, (int,), "-padding"))

    def __set__(self, instance: TkWidget, value: int | tuple[int, ...] | None):
        config(instance, padding=_convert_padding(value))
