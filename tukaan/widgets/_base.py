from __future__ import annotations

import collections
import contextlib
from typing import Any, DefaultDict, Iterator, Type

from tukaan._constants import _VALID_STATES
from tukaan._events import EventMixin
from tukaan._layouts import BaseLayoutManager, LayoutManager
from tukaan._structures import Bbox
from tukaan._tcl import Tcl
from tukaan._utils import _commands, _widgets, count, reversed_dict
from tukaan._variables import String


class ChildStatistics:
    def __init__(self, widget) -> None:
        self._widget = widget

    def number_of_type(self, type) -> int:
        try:
            return int(self._widget._child_type_count[type])
        except KeyError:
            return 0

    @property
    def children(self) -> list[BaseWidget]:
        return list(self._widget._children.values())

    @property
    def grid_managed_children(self) -> tuple:
        return tuple(
            self._widget.__from_tcl__(elem) for elem in Tcl.call((str,), "grid", "slaves", self._widget)
        )

    @property
    def position_managed_children(self) -> tuple:
        return tuple(
            self._widget.__from_tcl__(elem)
            for elem in Tcl.call((str,), "place", "slaves", self._widget)
        )


class WidgetMixin:
    def __repr__(self) -> str:
        details = self._repr_details()
        return (
            f"<tukaan.{type(self).__name__} widget:"
            + f" tcl_name={self._name!r}{', ' + details if details else ''}>"
        )

    def _repr_details(self) -> str:
        # overridden in subclasses
        return ""

    @property
    def id(self) -> int:
        return Tcl.call(int, "winfo", "id", self._name)

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> TkWidget:
        # unlike in teek, this method won't raise a TypeError,
        # if the return widget, and the class you call it on isn't the same
        # this could be annoying, but very useful if you don't know
        # what kind of widget it is and just want to get it

        # teek.Button.from_tcl(teek.Label().to_tcl())
        # >>> TypeError: blablabla

        # tukaan.Button.__from_tcl__(tukaan.Label().__to_tcl__())
        # >>> '.app.label_1'

        return _widgets[tcl_value]

    def __to_tcl__(self) -> str:
        return self._name


class ConfigMixin:
    _keys: dict[str, Any | tuple[Any, str]]

    def _cget(self, key: str) -> Any:
        if key in self._keys:
            if isinstance(self._keys[key], tuple):
                type_spec, key = self._keys[key]
            else:
                type_spec = self._keys[key]
        else:
            type_spec = str

        if type_spec == "func":
            # Return a Python callable, not a Tcl procedure name
            return _commands[self._get(str, key)]

        if isinstance(type_spec, dict):
            return reversed_dict(type_spec)[self._get(str, key)]

        return self._get(type_spec, key)

    def config(self, **kwargs) -> None:
        for key, value in tuple(kwargs.items()):
            if key in self._keys and isinstance(self._keys[key], tuple):
                # If the key has an alias in Tukaan, use the tuple[1] as the Tcl key
                type_spec, tcl_name = self._keys[key]
                value = kwargs.pop(key)

                if isinstance(type_spec, dict):
                    value = type_spec[value]

                kwargs[tcl_name] = value

            if key == "text":
                if isinstance(value, String):
                    kwargs["textvariable"] = kwargs.pop("text")
                else:
                    kwargs["textvariable"] = ""

        self._set(**kwargs)

    def _get(self, type_spec, key):
        return Tcl.call(type_spec, self, "cget", f"-{key}")

    def _set(self, **kwargs):
        Tcl.call(None, self, "configure", *Tcl.to_tcl_args(**kwargs))


class GetSetAttrMixin(ConfigMixin):
    _keys: dict[str, Any | tuple[Any, str]] = {}

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._keys:
            self.config(**{key: value})
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key: str) -> Any:
        if key in self._keys:
            return self._cget(key)
        else:
            return super().__getattribute__(key)


class StateMixin:
    @property
    def is_busy(self) -> bool:
        return Tcl.call(bool, "tk", "busy", "status", self)

    @is_busy.setter
    def is_busy(self, is_busy) -> None:
        if is_busy:
            Tcl.call(None, "tk", "busy", "hold", self)
        else:
            Tcl.call(None, "tk", "busy", "forget", self)

    @contextlib.contextmanager
    def busy(self):
        self.is_busy = True
        try:
            yield
        finally:
            self.is_busy = False

    def focus(self):
        Tcl.call(None, "focus", self)


class SizePosMixin:
    @property
    @Tcl.update_before
    def bbox(self) -> tuple:
        return Bbox(self._abs_x(), self._abs_y(), self._width(), self._height())

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

    rel_x = property(Tcl.update_before(_rel_x))
    rel_y = property(Tcl.update_before(_rel_y))
    abs_x = property(Tcl.update_before(_abs_x))
    abs_y = property(Tcl.update_before(_abs_y))
    width = property(Tcl.update_before(_width))
    height = property(Tcl.update_before(_height))


class VisibilityMixin:
    @property
    @Tcl.update_before
    def visible(self) -> bool:
        return Tcl.call(bool, "winfo", "ismapped", self._name)

    def hide(self):
        if self.layout._real_manager == "grid":
            # widget managed by grid
            Tcl.call(None, "grid", "remove", self._name)
        elif self.layout._real_manager == "place":
            # widget managed by position (place)
            # unfortunately there's no 'place remove' so it's kinda pain to keep the attributes
            self._temp_position_info = Tcl.call(
                {"-x": int, "-y": int, "-anchor": str, "-width": int, "-height": int},
                "place",
                "info",
                self._name,
            )
            Tcl.call(None, "place", "forget", self._name)

    def unhide(self):
        if self.layout._real_manager == "grid":
            # widget managed by grid
            Tcl.call(None, "grid", "configure", self._name)
        elif self.layout._real_manager == "place":
            # widget managed by position (place)
            Tcl.call(
                None,
                "place",
                "configure",
                self._name,
                *(
                    elem
                    for key, value in self._temp_position_info.items()
                    for elem in (key, value)
                    if value is not None
                ),
            )


class DnDMixin:
    def set_drag_target(self) -> None:
        Tcl.call(None, "tkdnd::drop_target", "register", self, "*")

    def unset_drag_target(self) -> None:
        Tcl.call(None, "tkdnd::drop_target", "unregister", self)

    def set_drag_source(self) -> None:
        Tcl.call(None, "tkdnd::drag_source", "register", self, "*")

    def unset_drag_source(self) -> None:
        Tcl.call(None, "tkdnd::drag_source", "unregister", self)


class TukaanWidget:
    """Base class for every Tukaan widget"""

    ...


class TkWidget(TukaanWidget, GetSetAttrMixin, WidgetMixin, EventMixin):
    """Base class for every Tk widget"""

    layout: BaseLayoutManager

    def __init__(self):
        _widgets[self._name] = self

        self._children: dict[str, BaseWidget] = {}
        self._child_type_count: DefaultDict[
            Type[BaseWidget], Iterator[int]
        ] = collections.defaultdict(lambda: count())
        self.child_stats = ChildStatistics(self)


class StateSet(collections.abc.MutableSet):
    """
    Object that contains the state of the widget
    """

    def __init__(self, widget: TkWidget) -> None:
        self._widget = widget

    def __repr__(self) -> str:
        return f"<state object of {self._widget}: state={list(self)}>"

    def __iter__(self) -> Iterator[str]:
        return iter(Tcl.call([str], self._widget, "state"))

    def __len__(self) -> int:
        return len(Tcl.call([str], self._widget, "state"))

    def __contains__(self, state: object) -> bool:
        return Tcl.call(bool, self._widget, "instate", state)

    def add_or_discard(self, action: str, state: str) -> None:
        assert state in _VALID_STATES

        if action == "discard":
            state = f"!{state}"

        Tcl.call(None, self._widget, "state", state)

    def add(self, state: str) -> None:
        self.add_or_discard("add", state)

    def discard(self, state: str) -> None:
        self.add_or_discard("discard", state)

    def __add__(self, other: str) -> StateSet:
        self.add(other)
        return self

    def __sub__(self, other: str) -> StateSet:  # type: ignore[override]
        self.discard(other)
        return self


class BaseWidget(TkWidget, StateMixin, DnDMixin, SizePosMixin, VisibilityMixin):
    layout: LayoutManager

    def __init__(
        self, parent: TkWidget | None, creation_cmd: tuple[TkWidget | str, ...] = None, **kwargs
    ) -> None:
        self.parent = parent
        self._name = self._give_me_a_name()

        TkWidget.__init__(self)

        self.parent._children[self._name] = self

        if not creation_cmd:
            Tcl.call(None, self._tcl_class, self._name, *Tcl.to_tcl_args(**kwargs))
        else:
            Tcl.call(None, *creation_cmd, *Tcl.to_tcl_args(**kwargs))

        self.layout = LayoutManager(self)
        self._temp_manager = None

        if self._tcl_class.startswith("ttk::"):
            self.state = StateSet(self)
        # else:
        #     need to define separately for non-ttk widgets

    def _give_me_a_name(self) -> str:
        klass = type(self)
        count = next(self.parent._child_type_count[klass])

        return f"{self.parent._name}.{klass.__name__.lower()}_{count}"

    def destroy(self):
        for child in self.child_stats.children:
            child.destroy()

        Tcl.call(None, "destroy", self._name)
        del self.parent._children[self._name]
        del _widgets[self._name]
