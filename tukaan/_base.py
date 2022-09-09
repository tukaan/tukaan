from __future__ import annotations

import collections
from typing import Callable

from ._events import EventMixin
from ._layout import ContainerGrid, Geometry, Grid, Position, ToplevelGrid
from ._mixins import DnDMixin, GeometryMixin, VisibilityMixin, WidgetMixin
from ._props import cget, config
from ._tcl import Tcl
from ._utils import _commands, _widgets, count
from ._wm import WindowManager
from .widgets.tooltip import ToolTipProvider


def generate_pathname(widget: TkWidget, parent: TkWidget) -> str:
    klass = widget.__class__
    count = next(parent._child_type_count[klass])

    return ".".join([parent._name, f"{klass.__name__.lower()}_{count}"])


class Container:
    ...


class InputControl:
    ...


class OutputDisplay:
    ...


class XScrollable:
    def x_scroll(self, *args) -> None:
        Tcl.call(None, self, "xview", *args)

    @property
    def on_xscroll(self) -> Callable:
        return _commands[cget(self, str, "-xscrollcommand")]

    @on_xscroll.setter
    def on_xscroll(self, value: Callable) -> None:
        config(self, xscrollcommand=value)


class YScrollable:
    def y_scroll(self, *args) -> None:
        Tcl.call(None, self, "yview", *args)

    @property
    def on_yscroll(self) -> Callable:
        return _commands[cget(self, str, "-yscrollcommand")]

    @on_yscroll.setter
    def on_yscroll(self, value: Callable) -> None:
        config(self, yscrollcommand=value)


class TkWidget(WidgetMixin, EventMixin, VisibilityMixin, DnDMixin):
    """Base class for every Tk widget"""

    _name: str
    _tcl_class: str

    def __init__(self):
        self._children = {}
        self._child_type_count = collections.defaultdict(lambda: count())

        _widgets[self._name] = self


class WindowBase(TkWidget, WindowManager, Container):
    def __init__(self):
        self.grid = ToplevelGrid(self)

        TkWidget.__init__(self)


class WidgetBase(TkWidget, GeometryMixin):
    def __init__(self, parent: TkWidget, tooltip: str | None = None, **kwargs):
        assert isinstance(parent, Container), "parent must be a container"

        self._name = self._lm_path = generate_pathname(self, parent)
        self.parent = parent
        self.parent._children[self._name] = self

        TkWidget.__init__(self)

        self.layout_manager = None
        self.grid = ContainerGrid(self) if isinstance(self, Container) else Grid(self)
        self.geometry = Geometry(self)
        self.position = Position(self)

        Tcl.call(None, self._tcl_class, self._name, *Tcl.to_tcl_args(**kwargs))

        if tooltip:
            ToolTipProvider.add(self, tooltip)

    def destroy(self):
        """Destroys this widget, and removes it from the screen"""

        Tcl.call(None, "destroy", self._name)

        del self.parent._children[self._name]
        del _widgets[self._name]

    @property
    def tooltip(self) -> str | None:
        return ToolTipProvider.get(self)

    @tooltip.setter
    def tooltip(self, value: str | None) -> None:
        ToolTipProvider.update(self, value)
