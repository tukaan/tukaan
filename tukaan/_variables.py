from __future__ import annotations

from typing import Generic

from tukaan._collect import counter, variables
from tukaan._tcl import Tcl
from tukaan._typing import T


class ControlVariable(Generic[T]):
    _default: T
    _type_spec: type[T]

    def __init__(self, value: T | None = None) -> None:
        self._type_spec = type(self._default)
        self._name = f"tukaan_{self._type_spec.__name__}var_{next(counter['variable'])}"
        variables[self._name] = self

        if value is None:
            value = self._default

        self.set(value)

    def __repr__(self) -> str:
        return f"<tukaan.{type(self).__name__} (tcl_name={self._name}, value={self.get()!r})>"

    def __hash__(self) -> int:
        return hash((self._type_spec, self._name))

    @classmethod
    def __from_tcl__(cls, value: str) -> ControlVariable[T]:
        return variables[value]

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
