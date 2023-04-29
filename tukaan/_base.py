from __future__ import annotations

import collections
from typing import Any, Callable

from tukaan._collect import commands, widgets
from tukaan._events import BindingsMixin
from tukaan._mixins import GeometryMixin, VisibilityMixin, WidgetMixin
from tukaan.layouts import LayoutManagerBase
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

    grid: LayoutManagerBase

    def __init__(self) -> None:
        self._children = {}
        self._child_type_count = collections.defaultdict(lambda: count())

        for name, lm in LayoutManagerBase.layout_managers.items():
            setattr(self, name, lm(self))

        widgets[self._name] = self


class ToplevelBase(TkWidget, Container):
    def __init__(self) -> None:
        TkWidget.__init__(self)


class WidgetBase(TkWidget, GeometryMixin):
    def __init__(self, parent: TkWidget, tooltip: str | None = None, **kwargs: Any) -> None:
        assert isinstance(parent, Container), "parent must be a container"

        self._name = self._lm_path = generate_pathname(self, parent)
        self.parent = parent
        self.parent._children[self._name] = self

        TkWidget.__init__(self)

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
