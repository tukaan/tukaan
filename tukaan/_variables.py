from __future__ import annotations

import numbers
from typing import Generic

from tukaan._collect import collector
from tukaan._tcl import Tcl
from tukaan._typing import T


class ControlVariable(Generic[T]):
    _default: T
    _type_spec: type[T]

    def __init__(self, value: T | None = None) -> None:
        self._type_spec = type(self._default)
        self._name = collector.add("control_variable", self)

        self.set(self._default if value is None else value)

    def __repr__(self) -> str:
        return f"<tukaan.{type(self).__name__} tcl_name={self._name}, value={self.get()!r}>"

    def __hash__(self) -> int:
        return hash((self._type_spec, self._name))

    @staticmethod
    def __from_tcl__(value: str) -> ControlVariable:
        return collector.get_by_key("control_variable", value)

    @staticmethod
    def get_class_for_type(value: T) -> type[ControlVariable]:
        if isinstance(value, str):
            return StringVar
        elif isinstance(value, bool):
            return BoolVar
        elif isinstance(value, int):
            return IntVar
        elif isinstance(value, numbers.Real):
            return FloatVar
        else:
            raise TypeError(f"invalid value: {value!r}")

    def set(self, value: T) -> None:
        Tcl.call(None, "set", self._name, value)

    def get(self) -> T:
        return Tcl.call(self._type_spec, "set", self._name)

    @property
    def value(self) -> T:
        return self.get()

    @value.setter
    def value(self, value: T) -> None:
        self.set(value)


class StringVar(ControlVariable[str]):
    _default = ""


class IntVar(ControlVariable[int]):
    _default = 0


class FloatVar(ControlVariable[float]):
    _default = 0.0


class BoolVar(ControlVariable[bool]):
    _default = False
