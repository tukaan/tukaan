from __future__ import annotations

from tukaan._collect import _variables, counter
from tukaan._tcl import Tcl


class ControlVariable:
    # FIXME: typing in this file

    _type_spec: type[float | str | bool]
    _default: float | str | bool

    def __init__(self, value: float | str | bool | None = None) -> None:
        self._name = f"tukaan_{self._type_spec.__name__}var_{next(counter['variable'])}"
        _variables[self._name] = self

        if value is None:
            value = self._default

        self.set(value)

    def __repr__(self) -> str:
        return f"<tukaan.{type(self).__name__} control variable: tcl_name={self._name}, value={self.get()!r}>"

    def __hash__(self) -> None:
        return hash((self._type_spec, self._name))

    @classmethod
    def __from_tcl__(cls, value: str) -> ControlVariable:
        return _variables[value]

    def set(self, value: float | str | bool) -> None:
        Tcl.call(None, "set", self._name, value)

    def get(self):
        return Tcl.call(self._type_spec, "set", self._name)

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value: float | str | bool) -> None:
        self.set(value)


class StringVar(ControlVariable):
    _type_spec = str
    _default = ""


class IntVar(ControlVariable):
    _type_spec = int
    _default = 0


class FloatVar(ControlVariable):
    _type_spec = float
    _default = 0.0


class BoolVar(ControlVariable):
    _type_spec = bool
    _default = False
