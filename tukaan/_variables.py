from __future__ import annotations

from ._utils import _variables, counts, get_tcl_interp


class _TclVariable:
    _type_spec: type
    _default: float | str | bool

    def __init__(self, value=None, name=None):
        if name is None:
            name = f"tukaan_{self._type_spec.__name__}_var_{next(counts['variable'])}"

        if value is None:
            value = self._default

        self._name = name
        _variables[name] = self
        self.set(value)

    def __repr__(self):
        return f"tukaan.{type(self).__name__} control variable: tcl_name={self._name}, value={self.get()!r}"

    __str__ = __repr__

    def __hash__(self):
        return hash((self._type_spec, self._name))

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value):
        return _variables[value]

    def set(self, new_value) -> None:
        get_tcl_interp()._tcl_call(None, "set", self._name, new_value)

    def get(self):
        return get_tcl_interp()._tcl_call(self._type_spec, "set", self._name)

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value: float | str | bool):
        self.set(value)

    def wait(self) -> None:
        get_tcl_interp()._tcl_call(None, "tkwait", "variable", self._name)


class String(_TclVariable):
    _type_spec = str
    _default = ""

    def __iadd__(self, string: str) -> String:
        # ???
        self.set(self.get() + string)
        return self


class Integer(_TclVariable):
    _type_spec = int
    _default = 0


class Float(_TclVariable):
    _type_spec = float
    _default = 0.0


class Boolean(_TclVariable):
    _type_spec = bool
    _default = False
