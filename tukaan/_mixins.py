from __future__ import annotations

from typing import TYPE_CHECKING

from tukaan._collect import _widgets
from tukaan._layout import Grid
from tukaan._misc import Bbox
from tukaan._tcl import Tcl

if TYPE_CHECKING:
    from tukaan._base import TkWidget


class WidgetMixin:
    _name: str

    def __repr__(self) -> str:
        klass = type(self).__name__
        details = self._repr_details()
        details = f", {details}" if details else ""

        return f"<{klass} widget at {hex(id(self))}: tcl_name={self._name!r}{details}>"

    def _repr_details(self) -> str:
        # overridden in subclasses
        return ""

    @property
    def id(self) -> int:
        return Tcl.call(int, "winfo", "id", self._name)

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> TkWidget:
        return _widgets[tcl_value]


class GeometryMixin:
    def _abs_x(self) -> int:
        return Tcl.call(int, "winfo", "rootx", self)

    def _abs_y(self) -> int:
        return Tcl.call(int, "winfo", "rooty", self)

    def _rel_x(self) -> int:
        return Tcl.call(int, "winfo", "x", self)

    def _rel_y(self) -> int:
        return Tcl.call(int, "winfo", "y", self)

    def _width(self) -> int:
        return Tcl.call(int, "winfo", "reqwidth", self)

    def _height(self) -> int:
        return Tcl.call(int, "winfo", "reqheight", self)

    @property
    @Tcl.redraw_before
    def bbox(self) -> tuple:
        return Bbox(self._abs_x(), self._abs_y(), self._width(), self._height())

    rel_x = property(Tcl.redraw_before(_rel_x))
    rel_y = property(Tcl.redraw_before(_rel_y))
    abs_x = property(Tcl.redraw_before(_abs_x))
    abs_y = property(Tcl.redraw_before(_abs_y))
    width = property(Tcl.redraw_before(_width))
    height = property(Tcl.redraw_before(_height))


class VisibilityMixin:
    @property
    @Tcl.redraw_before
    def visible(self) -> bool:
        return Tcl.call(bool, "winfo", "ismapped", self)

    @visible.setter
    def visible(self, value: bool) -> None:
        if value:
            self.unhide()
        else:
            self.hide()

    def hide(self):
        if self.layout_manager is Grid:
            self.grid._hide()
        else:
            raise NotImplementedError("cannot hide element with this layout manager")

    def unhide(self):
        if self.layout_manager is Grid:
            self.grid._unhide()
        else:
            raise NotImplementedError("cannot hide element with this layout manager")
