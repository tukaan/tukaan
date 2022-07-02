from __future__ import annotations

from ._tcl import Tcl
from ._utils import _variables, counts


class ControlVariable:
    _type_spec: type
    _default: float | str | bool

    def __init__(self, value=None, name=None):
        if name is None:
            name = f"tukaan_{self._type_spec.__name__}_var_{next(counts['variable'])}"

        if value is None:
            value = self._default

        _variables[name] = self
        self._name = name
        self.set(value)

    def __repr__(self):
        return f"tukaan.{type(self).__name__} control variable: tcl_name={self._name}, value={self.get()!r}"

    __str__ = __repr__

    def __hash__(self):
        return hash((self._type_spec, self._name))

    def __to_tcl__(self):
        return self._name

    @classmethod
    def __from_tcl__(cls, value):
        return _variables[value]

    def set(self, new_value):
        return Tcl.call(self._type_spec, "set", self._name, new_value)

    def get(self):
        return Tcl.call(self._type_spec, "set", self._name)

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value: float | str | bool):
        self.set(value)


class String(ControlVariable):
    _type_spec = str
    _default = ""


class Integer(ControlVariable):
    _type_spec = int
    _default = 0


class Float(ControlVariable):
    _type_spec = float
    _default = 0.0


class Boolean(ControlVariable):
    _type_spec = bool
    _default = False

    def __invert__(self) -> bool:
        inverted = not Tcl.call(bool, "set", self._name)
        Tcl.call(None, "set", self._name, inverted)
        return inverted
