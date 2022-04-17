from __future__ import annotations

import collections
import contextlib
from typing import Any, DefaultDict, Iterator

from tukaan._events import EventMixin
from tukaan._layouts import ContainerLayoutManager, PackableLayoutManager
from tukaan._structures import Bbox
from tukaan._tcl import Tcl
from tukaan._utils import _commands, _widgets, count, reversed_dict
from tukaan._variables import _TclVariable


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
            self._widget.__from_tcl__(elem)
            for elem in Tcl.call((str,), "grid", "slaves", self._widget)
        )

    @property
    def position_managed_children(self) -> tuple:
        return tuple(
            self._widget.__from_tcl__(elem)
            for elem in Tcl.call((str,), "place", "slaves", self._widget)
        )


class StateSet:
    def __init__(self, widget: TkWidget) -> None:
        self._widget = widget

    def __repr__(self) -> str:
        return str(set(self))

    def __iter__(self) -> Iterator[str]:
        tcl_state = Tcl.call((str,), self._widget, "state")
        if tcl_state:
            return iter(tcl_state)
        yield None

    def __len__(self) -> int:
        return len(set(self))

    def __contains__(self, state: str) -> bool:
        return Tcl.call(bool, self._widget, "instate", state)

    def __or__(self, state: str) -> StateSet:
        Tcl.call(None, self._widget, "state", state)
        return self

    def __sub__(self, state: str) -> StateSet:
        Tcl.call(None, self._widget, "state", "!" + state)
        return self


class ConfigMixin:
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
                if isinstance(value, _TclVariable):
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


class XScrollable:
    def x_scroll(self, *args) -> None:
        Tcl.call(None, self, "xview", *args)


class YScrollable:
    def y_scroll(self, *args) -> None:
        Tcl.call(None, self, "yview", *args)


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

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> TkWidget:
        return _widgets[tcl_value]


class TukaanWidget:
    """Base class for every Tukaan widget"""

    ...


class TkWidget(TukaanWidget, GetSetAttrMixin, WidgetMixin, EventMixin):
    """Base class for every Tk widget"""

    layout: ContainerLayoutManager

    def __init__(self):
        _widgets[self._name] = self

        self._children: dict[str, BaseWidget] = {}
        self._child_type_count: DefaultDict[
            type[BaseWidget], Iterator[int]
        ] = collections.defaultdict(lambda: count())
        self.child_stats = ChildStatistics(self)


class BaseWidget(TkWidget, StateMixin, DnDMixin, SizePosMixin, VisibilityMixin):
    layout: PackableLayoutManager

    def __init__(
        self, parent: TkWidget, creation_cmd: tuple[TkWidget | str, ...] = None, **kwargs
    ) -> None:
        assert isinstance(parent, TkWidget), "parent must be a TkWidget instance"

        self._name = self._give_me_a_name(parent)
        self.parent = parent

        TkWidget.__init__(self)

        self.parent._children[self._name] = self

        if not creation_cmd:
            Tcl.call(None, self._tcl_class, self._name, *Tcl.to_tcl_args(**kwargs))
        else:
            Tcl.call(None, *creation_cmd, *Tcl.to_tcl_args(**kwargs))

        self.layout = PackableLayoutManager(self)
        self._temp_manager = None

        if self._tcl_class.startswith("ttk::"):
            self.state = StateSet(self)
        # else:
        #     need to define separately for non-ttk widgets

    def _give_me_a_name(self, parent: TkWidget) -> str:
        class_ = type(self)
        count = next(parent._child_type_count[class_])
        return f"{parent._name}.{class_.__name__.lower()}_{count}"

    def destroy(self):
        for child in self.child_stats.children:
            child.destroy()

        Tcl.call(None, "destroy", self._name)
        del self.parent._children[self._name]
        del _widgets[self._name]


class ContainerWidget:
    ...


class InputControlWidget:
    ...


class OutputDisplayWidget:
    ...
