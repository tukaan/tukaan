from __future__ import annotations

import collections.abc
import contextlib
from typing import Any, Callable, Iterator

from ._layouts import LayoutManager
from ._returntype import Callback, DictKey
from ._utils import (
    _callbacks,
    _widgets,
    get_tcl_interp,
    py_to_tcl_arguments,
    update_before,
)


class ChildStatistics:
    def __init__(self, widget) -> None:
        self._widget = widget

    def number_of_type(self, type) -> int:
        try:
            return self._widget._child_type_count[type]
        except KeyError:
            return 0

    @property
    def children(self) -> list:
        return list(self._widget._children.values())

    @property
    def grid_managed_children(self) -> tuple:
        return tuple(
            self._widget.from_tcl(elem)
            for elem in self._widget._tcl_call((str,), "grid", "slaves", self._widget)
        )

    @property
    def position_managed_children(self) -> tuple:
        return tuple(
            self._widget.from_tcl(elem)
            for elem in self._widget._tcl_call((str,), "place", "slaves", self._widget)
        )


class MethodAndPropMixin:
    _tcl_call: Callable
    _keys: dict[str, Any]
    tcl_path: str
    wm_path: str
    parent: TkWidget
    child_stats: ChildStatistics

    def __repr__(self) -> str:
        return (
            f"<tukaan.{type(self).__name__}"
            + " widget,"
            + f" id={self.tcl_path!r}{': ' + self._repr_details() if self._repr_details() else ''}>"
        )

    __str__ = __repr__

    def _repr_details(self) -> str:
        # overridden in subclasses
        return ""

    @property
    def is_busy(self) -> bool:
        return self._tcl_call(bool, "tk", "busy", "status", self)

    @is_busy.setter
    def is_busy(self, is_busy) -> None:
        if is_busy:
            self._tcl_call(None, "tk", "busy", "hold", self)
        else:
            self._tcl_call(None, "tk", "busy", "forget", self)

    @contextlib.contextmanager
    def busy(self):
        self.is_busy = True
        try:
            yield
        finally:
            self.is_busy = False

    @property
    def id(self) -> int:
        return self._tcl_call(int, "winfo", "id", self.tcl_path)

    def _cget(self, key: str) -> Any:
        if isinstance(self._keys[key], tuple):
            type_spec, key = self._keys[key]
        else:
            type_spec = self._keys[key]

        if type_spec is Callback:
            # return a callable func, not tcl name
            result = self._tcl_call(str, self, "cget", f"-{key}")
            return _callbacks[result]

        if isinstance(type_spec, DictKey):
            result = self._tcl_call(str, self, "cget", f"-{key}")
            return type_spec[result]

        return self._tcl_call(type_spec, self, "cget", f"-{key}")

    def config(self, **kwargs) -> None:
        for key in tuple(kwargs.keys()):
            if isinstance(self._keys[key], tuple):
                # if key has a tukaan alias, use the tuple's 2-nd item as the tcl key
                kwargs[self._keys[key][1]] = kwargs.pop(key)

        get_tcl_interp()._tcl_call(
            None, self, "configure", *py_to_tcl_arguments(**kwargs)
        )

    @classmethod
    def from_tcl(cls, tcl_value: str) -> TkWidget:
        # unlike in teek, this method won't raise a TypeError,
        # if the return widget, and the class you call it on isn't the same
        # this could be annoying, but very useful if you don't know
        # what kind of widget it is and just want to get it

        # teek.Button.from_tcl(teek.Label().to_tcl())
        # >>> TypeError: blablabla

        # tukaan.Button.from_tcl(teek.tukaan().to_tcl())
        # >>> '.app.label_1'

        if tcl_value == ".":
            return get_tcl_interp()

        return _widgets[tcl_value]

    def to_tcl(self) -> str:
        return self.tcl_path

    @property
    def _class(self):
        return self._tcl_call(str, "winfo", "class", self)

    @property
    def keys(self) -> list:
        return sorted(self._keys.keys())

    @property
    def bbox(self) -> tuple:
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property  # type: ignore
    @update_before
    def x(self) -> int:
        return self._tcl_call(int, "winfo", "rootx", self)

    @property  # type: ignore
    @update_before
    def y(self) -> int:
        return self._tcl_call(int, "winfo", "rooty", self)

    @property  # type: ignore
    @update_before
    def width(self) -> int:
        return self._tcl_call(int, "winfo", "width", self)

    @property  # type: ignore
    @update_before
    def height(self) -> int:
        return self._tcl_call(int, "winfo", "height", self)

    def hide(self):
        if self.tcl_path == ".app" or self._class == "Toplevel":
            self._tcl_call(None, "wm", "withdraw", self.wm_path)
        else:
            manager = self._tcl_call(str, "winfo", "manager", self)
            self._temp_manager = manager
            if manager == "grid":
                self._tcl_call(None, "grid", "remove", self.tcl_path)
            elif manager == "place":
                self._temp_position_info = self._tcl_call(
                    {
                        "-x": int,
                        "-y": int,
                        "-anchor": str,
                        "-width": int,
                        "-height": int,
                    },
                    "place",
                    "info",
                    self.tcl_path,
                )
                self._tcl_call(None, "place", "forget", self.tcl_path)

    def unhide(self):
        if self.tcl_path == ".app" or self._class == "Toplevel":
            self._tcl_call(None, "wm", "deiconify", self.wm_path)
        elif self._temp_manager == "grid":
            self._tcl_call(None, "grid", "configure", self.tcl_path)
        elif self._temp_manager == "place":
            self._tcl_call(
                None,
                (
                    "place",
                    "configure",
                    self.tcl_path,
                    *(
                        elem
                        for key, value in self._temp_position_info.items()
                        for elem in (key, value)
                        if value is not None
                    ),
                ),
            )


class TukaanWidget:
    """Base class for every Tukaan widget"""

    ...


class TkWidget(MethodAndPropMixin):
    """Base class for every Tk-based widget"""

    layout: LayoutManager

    def __init__(self):
        self._children: dict[str, TkWidget] = {}
        self._child_type_count: dict[type, int] = {}
        _widgets[self.tcl_path] = self
        self.child_stats = ChildStatistics(self)


class StateSet(collections.abc.MutableSet):
    """Object that contains the state of the widget, though it inherits from MutableSet, it behaves like a list"""

    def __init__(self, widget: TkWidget) -> None:
        self._widget = widget

    def __repr__(self) -> str:
        return f"<state object of {self._widget}: state={list(self)}>"

    def __iter__(self) -> Iterator[str]:
        return iter(self._widget._tcl_call([str], self._widget, "state"))

    def __len__(self) -> int:
        return len(self._widget._tcl_call([str], self._widget, "state"))

    def __contains__(self, state: object) -> bool:
        return self._widget._tcl_call(bool, self._widget, "instate", state)

    def add(self, state: str) -> None:
        self._widget._tcl_call(None, self._widget, "state", state)

    def discard(self, state: str) -> None:
        self._widget._tcl_call(None, self._widget, "state", f"!{state}")


class BaseWidget(TkWidget):
    _keys: dict[str, Any | tuple[Any, str]]

    def __init__(self, parent: TkWidget | None, widget_name: str, **kwargs) -> None:
        self.parent = parent or get_tcl_interp()
        self.tcl_path = self._give_me_a_name()
        self._tcl_call: Callable = get_tcl_interp()._tcl_call

        TkWidget.__init__(self)

        self.parent._children[self.tcl_path] = self

        self._tcl_call(None, widget_name, self.tcl_path, *py_to_tcl_arguments(**kwargs))

        self.layout = LayoutManager(self)
        self._temp_manager = None

        if self._class.startswith("ttk::"):
            self.state = StateSet(self)
        # else:
        #     need to define separately for non-ttk widgets

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._keys.keys():
            self.config(**{key: value})
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key: str) -> Any:
        if key in self._keys.keys():
            return self._cget(key)
        else:
            return super().__getattribute__(key)

    def _give_me_a_name(self) -> str:
        klass = type(self)

        # FIXME: more elegant way to count child types
        # itertools.count isn't good, because we need plain ints

        count = self.parent._child_type_count.get(klass, 0) + 1
        self.parent._child_type_count[klass] = count

        return f"{self.parent.tcl_path}.{klass.__name__.lower()}_{count}"

    def destroy(self):
        for child in self.child_stats.children:
            child.destroy()

        self._tcl_call(None, "destroy", self.tcl_path)
        del self.parent._children[self.tcl_path]
        del _widgets[self.tcl_path]
