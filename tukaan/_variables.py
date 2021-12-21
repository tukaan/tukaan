from __future__ import annotations

from ._utils import counts, _variables, get_tcl_interp


class _TclVariable:
    _type_spec: type
    
    def __init__(self, value, name=None):
        if name is None:
            name = f"tukaan_{self._type_spec.__name__}_var_{next(counts['variable'])}"

        self._name = name
        _variables[name] = self
        self.set(value)

    def __repr__(self):
        return str(self.get())

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

    def get(self) -> None:
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

    def __iadd__(self, string: str) -> String:
        # ???
        self.set(self.get() + string)
        return self
