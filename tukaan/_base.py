from __future__ import annotations

import collections
from typing import Any, Callable

from tukaan._collect import commands, widgets
from tukaan._events import BindingsMixin
from tukaan._layout import ContainerGrid, Geometry, Grid, LayoutManager, Position, ToplevelGrid
from tukaan._misc import Bbox
from tukaan._props import cget, config
from tukaan._tcl import Tcl
from tukaan._utils import count
from tukaan.widgets.tooltip import ToolTipProvider


def generate_pathname(widget: TkWidget, parent: TkWidget) -> str:
    klass = widget.__class__
    count = next(parent._child_type_count[klass])

    return ".".join((parent._name, f"{klass.__name__.lower()}_{count}"))


class Container:
    ...


class InputControl:
    ...


class OutputDisplay:
    ...


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
        return widgets[tcl_value]


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
    def bbox(self) -> Bbox:
        return Bbox(self._abs_x(), self._abs_y(), self._width(), self._height())

    rel_x = property(Tcl.redraw_before(_rel_x))
    rel_y = property(Tcl.redraw_before(_rel_y))
    abs_x = property(Tcl.redraw_before(_abs_x))
    abs_y = property(Tcl.redraw_before(_abs_y))
    width = property(Tcl.redraw_before(_width))
    height = property(Tcl.redraw_before(_height))


class VisibilityMixin:
    layout_manager: LayoutManager
    grid: Grid

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


class XScrollable:
    def x_scroll(self, *args: Any) -> None:
        Tcl.call(None, self, "xview", *args)

    @property
    def on_xscroll(self) -> Callable[..., Any]:
        return commands[cget(self, str, "-xscrollcommand")]

    @on_xscroll.setter
    def on_xscroll(self, value: Callable[..., Any]) -> None:
        config(self, xscrollcommand=value)


class YScrollable:
    def y_scroll(self, *args: Any) -> None:
        Tcl.call(None, self, "yview", *args)

    @property
    def on_yscroll(self) -> Callable[..., Any]:
        return commands[cget(self, str, "-yscrollcommand")]

    @on_yscroll.setter
    def on_yscroll(self, value: Callable[..., Any]) -> None:
        config(self, yscrollcommand=value)


class TkWidget(WidgetMixin, BindingsMixin, VisibilityMixin):
    """Base class for every Tk widget."""

    _name: str
    _tcl_class: str
    _variable: Any  # TODO This is set in LinkProp

    def __init__(self) -> None:
        self._children = {}
        self._child_type_count = collections.defaultdict(lambda: count())

        widgets[self._name] = self


class ToplevelBase(TkWidget, Container):
    def __init__(self) -> None:
        self.grid = ToplevelGrid(self)

        TkWidget.__init__(self)


class WidgetBase(TkWidget, GeometryMixin):
    def __init__(self, parent: TkWidget, tooltip: str | None = None, **kwargs: Any) -> None:
        assert isinstance(parent, Container), "parent must be a container"

        self._name = self._lm_path = generate_pathname(self, parent)
        self.parent = parent
        self.parent._children[self._name] = self

        TkWidget.__init__(self)

        self.grid = ContainerGrid(self) if isinstance(self, Container) else Grid(self)
        self.geometry = Geometry(self)
        self.position = Position(self)

        Tcl.call(None, self._tcl_class, self._name, *Tcl.to_tcl_args(**kwargs))

        if tooltip:
            ToolTipProvider.add(self, tooltip)

    def destroy(self) -> None:
        """Destroy this widget, and remove it from the screen."""
        Tcl.call(None, "destroy", self._name)

        del self.parent._children[self._name]
        del widgets[self._name]

    @property
    def tooltip(self) -> str | None:
        return ToolTipProvider.get(self)

    @tooltip.setter
    def tooltip(self, value: str | None) -> None:
        ToolTipProvider.update(self, value)
