from __future__ import annotations

from tukaan._helpers import convert_4side, convert_4side_back
from tukaan._tcl import Tcl

from ._base import BaseWidget, ContainerWidget, TkWidget


class Frame(BaseWidget, ContainerWidget):
    _tcl_class = "ttk::frame"
    _keys = {}

    def __init__(self, parent: TkWidget, padding: int | tuple[int, ...] | None = None) -> None:
        BaseWidget.__init__(self, parent, padding=convert_4side(padding))

    def _get(self, type_spec, key):
        if key == "padding":
            return self.padding
        else:
            return super()._get(type_spec, key)

    def _set(self, **kwargs):
        if "padding" in kwargs:
            self.padding = kwargs.pop("padding", (0,) * 4)

        super()._set(**kwargs)

    @property
    def padding(self):
        return convert_4side_back(tuple(map(int, Tcl.call((str,), self, "cget", "-padding"))))

    @padding.setter
    def padding(self, new_padding):
        Tcl.call(None, self, "configure", "-padding", convert_4side(new_padding))
