from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Iterator

from tukaan._collect import collector
from tukaan._tcl import Tcl
from tukaan._typing import T
from tukaan.layouts.base import LayoutManagerBase


class count:
    """Simplified itertools.count, that can be int()-ed."""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        yield self._count

    def __int__(self) -> int:
        return self._count


class TkWidget:
    _name: str
    _toplevel_name: str
    _widget_cmd: str
    _tk_class: str

    grid: LayoutManagerBase

    def __init__(self):
        self._child_type_count = defaultdict(lambda: count())

        for name, lm in LayoutManagerBase.layout_managers.items():
            setattr(self, name, lm(self._name, self._toplevel_name))

        name, toplevel_name = self._name, self._toplevel_name
        if name != toplevel_name:
            collector.add("widgets", self, name=toplevel_name)
        collector.add("widgets", self, name=name)

    @property
    def children(self) -> Iterator[TkWidget]:
        for child in Tcl.call((str,), "winfo", "children", self):
            yield Tcl.from_(TkWidget, child)

    @classmethod
    def __from_tcl__(cls, value: str) -> TkWidget:
        return collector.get_by_key("widgets", value)


class ToplevelWidget(TkWidget):
    def __init__(self) -> None:
        TkWidget.__init__(self)


class Widget(TkWidget):
    def __init_subclass__(cls, widget_cmd: str, tk_class: str) -> None:
        cls._widget_cmd = widget_cmd
        cls._tk_class = tk_class

    def __init__(self, parent: TkWidget, **kwargs):
        py_widget_class_name = type(self).__name__.lower()
        try:
            count = next(parent._child_type_count[py_widget_class_name])
        except AttributeError:
            raise TypeError from None

        self._name = self._toplevel_name = f"{parent._name}.{py_widget_class_name}_{count}"

        TkWidget.__init__(self)

        kwargs["class"] = self._tk_class
        Tcl.call(None, self._widget_cmd, self._name, *Tcl.to_tcl_args(**kwargs))
        self.parent = parent

    def destroy(self) -> None:
        """Destroy this widget."""
        Tcl.call(None, "destroy", self._name)
        collector.remove_by_key("widgets", self._name)

    def finalize_megawidget(self, name: str) -> None:
        self._name = name
        for lm_name in LayoutManagerBase.layout_managers:
            getattr(self, lm_name)._owner_name = name
