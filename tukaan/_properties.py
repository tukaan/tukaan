from __future__ import annotations

import sys
from enum import Enum, EnumType
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

if sys.version_info >= (3, 9):
    from collections.abc import Callable
    from typing import Protocol
else:
    from typing import Callable
    from typing_extensions import Protocol

from tukaan._base import TkWidget
from tukaan._tcl import Procedure, Tcl
from tukaan._typing import P, PaddingType, T, T_co, T_contra
from tukaan._variables import ControlVariable


def cget(widget: TkWidget, return_type: T | type[T], option: str) -> T:
    return Tcl.call(return_type, widget, "cget", option)


def config(widget: TkWidget, **kwargs: Any) -> None:
    assert len(kwargs) == 1

    [(key, value)] = kwargs.items()
    Tcl.call(None, widget, "configure", f"-{key}", value if value is not None else "")


class RWProperty(Protocol[T_co, T_contra]):
    def __get__(self, instance: TkWidget, owner: object = None) -> T_co:
        ...

    def __set__(self, instance: TkWidget, value: T_contra) -> None:
        ...


class OptionDescriptor(RWProperty[T, T_contra]):
    def __init__(self, option: str, type_: type[T]) -> None:
        self._option = option
        self._type = type_

    def __get__(self, instance: TkWidget, owner: object = None) -> T:
        if owner is None:
            return NotImplemented
        return cget(instance, self._type, f"-{self._option}")

    def __set__(self, instance: TkWidget, value: T_contra) -> None:
        config(instance, **{self._option: value})


class DynamicProperty:
    def __set_name__(self, owner: type[TkWidget], name: str) -> None:
        self._name = name
        if not self._option:
            self._option = name


class IntDesc(OptionDescriptor[int, int], DynamicProperty):
    def __init__(self, option: str = "") -> None:
        super().__init__(option, int)

    def __get__(self, instance: TkWidget, owner: object = None) -> int:
        if owner is None:
            return NotImplemented
        return int(cget(instance, float, f"-{self._option}"))


class FloatDesc(OptionDescriptor[float, float], DynamicProperty):
    def __init__(self, option: str = "") -> None:
        super().__init__(option, float)


class BoolDesc(OptionDescriptor[bool, bool], DynamicProperty):
    def __init__(self, option: str = "") -> None:
        super().__init__(option, bool)


class StrDesc(OptionDescriptor[str, str], DynamicProperty):
    def __init__(self, option: str = "") -> None:
        super().__init__(option, str)


class EnumDesc(OptionDescriptor[Enum, Enum], DynamicProperty):
    def __init__(self, option: str = "", enum: EnumType | None = None, allow_None: bool = True) -> None:
        assert enum is not None, "use the `enum` kwarg to set the enum for an EnumDesc"
        self._allow_None = allow_None
        super().__init__(option, enum)  # type: ignore

    def __set__(self, instance: TkWidget, value: T_contra) -> None:
        if value is None and not self._allow_None:
            raise TypeError(f"value for {type(instance).__name__}.{self._name} must be a member of {self._type!r}")
        super().__set__(instance, value)


class FocusableProp(BoolDesc):
    # FIXME: the current behavior isn't right
    # It should also work with a Callable[[TkWidget], bool]
    def __init__(self) -> None:
        super().__init__("takefocus")

    def __get__(self, instance: TkWidget, owner: object = None) -> bool:
        if owner is None:
            return NotImplemented
        result: str = Tcl.call(str, instance, "cget", "-takefocus")
        if result not in ("", "0", "1"):
            return Tcl.call(bool, result, instance)
        return Tcl.from_(bool, result)


class ActionProp(OptionDescriptor[Procedure, Optional[Callable[P, T]]]):
    def __init__(self, option: str = "command") -> None:
        super().__init__(option, Procedure)


class LinkProp(RWProperty[ControlVariable[T], Optional[ControlVariable[T]]]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return cget(instance, ControlVariable, "-variable")

    def __set__(self, instance: TkWidget, value: ControlVariable[T] | TkWidget | None) -> None:
        if isinstance(value, TkWidget):
            value = value._variable
        instance._variable = value
        return config(instance, variable=value or "")


def convert_padding_to_tk(padding: PaddingType) -> tuple[int, ...] | str:
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


def convert_padding_back(padding: tuple[int, ...]) -> Tuple[int, int, int, int]:
    if len(padding) == 1:
        return (padding[0],) * 4
    elif len(padding) == 4:
        return (padding[1], padding[2], padding[3], padding[0])

    return (0,) * 4


class PaddingProp(RWProperty[Tuple[int, int, int, int], PaddingType]):
    def __get__(self, instance: TkWidget, owner: object = None):
        if owner is None:
            return NotImplemented
        return convert_padding_back(cget(instance, (int,), "-padding"))

    def __set__(self, instance: TkWidget, value: PaddingType) -> None:
        config(instance, padding=convert_padding_to_tk(value))
