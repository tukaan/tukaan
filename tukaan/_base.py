import collections
import itertools
from abc import abstractmethod

from .utils import get_tcl_interp, update_after, update_before, updated, create_command

from typing import Callable, Union, Any, Dict, Tuple, List



class ChildStatistics:
    def __init__(self, widget) -> None:
        self._widget = widget

    def number_of_type(self, type) -> int:
        try:
            return self._widget._child_type_count[type]
        except KeyError:
            print("ok")
            return 0

    @property
    def children(cls) -> list:
        return list(cls._widget._children.values())


class StateSet(collections.abc.MutableSet):
    """Object that contains the state of the widget, though it inherits from MutableSet, it behaves like a dict"""
    __tk_widgets: set = {"text"}

    def __init__(self, widget) -> None:
        self._widget = widget

    def __repr__(self) -> list:
        return list(self)

    def __iter__(self) -> str:
        return iter(self._widget._tcl_call([str], self._widget, "state"))

    def __len__(self) -> int:
        if self._widget._class not in self.__tk_widgets:
            return len(self._widget._tcl_call([str], self._widget, "state"))
        else:
            return 1

    def __contains__(self, state) -> bool:
        if self._widget._class not in self.__tk_widgets:
            return self._widget._tcl_call(bool, self._widget, "instate", state)
        else:
            return self._widget._tcl_call(str, self._widget, "cget", "-state") == state

    def add(self, state) -> None:
        if self._widget._class not in self.__tk_widgets:
            self._widget._tcl_call(None, self._widget, "state", state)
        else:
            self._widget._tcl_call(None, self._widget, "config", "-state", state)

    def discard(self, state) -> None:
        if self._widget._class not in self.__tk_widgets:
            self._widget._tcl_call(None, self._widget, "state", f"!{state}")
        else:
            self._widget._tcl_call(None, self._widget, "config", "-state", "normal")




# FIXME: MethodMixin isn't a good nam, because it contains mostly properties
class MethodMixin:
    _tcl_call: Callable


    def __repr__(self) -> str:
        return f"<tukaan.{type(self).__name__} widget{': ' + self._repr_details() if self._repr_details() else ''}>"

    __str__ = __repr__

    def _repr_details(self) -> Union[str, None]:
        # overriden in subclasses
        return None

    @property
    def busy(self) -> bool:
        return self._tcl_call(bool, "tk", "busy", "status", self)

    @busy.setter
    def busy(self, is_busy) -> None:
        if is_busy:
            self._tcl_call(None, "tk", "busy", "hold", self)
        else:
            self._tcl_call(None, "tk", "busy", "forget", self)

    @property
    def id(self) -> int:
        return self._tcl_call(int, "winfo", "id", self.tcl_path)

    def _cget(self, key):
        if isinstance(self._keys[key], tuple):
            type_spec, key = self._keys[key]
        else:
            type_spec = self._keys[key]

        return self._tcl_call(type_spec, self, "cget", f"-{key}")

    @update_after
    def config(self, **kwargs) -> None:
        get_tcl_interp().tcl_call(
            None, self, "configure", *self._py_to_tcl_arguments(kwargs)
        )

    def to_tcl(self) -> str:
        return self.tcl_path

    @property
    def _class(self):
        return self._tcl_call(str, "winfo", "class", self)

    @property
    def keys(self) -> list:
        return sorted(self._keys)

    @property
    def bbox(self) -> tuple:
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    @update_before
    def x(self) -> int:
        return self._tcl_call(int, "winfo", "rootx", self)

    @property
    @update_before
    def y(self) -> int:
        return self._tcl_call(int, "winfo", "rooty", self)

    @property
    @update_before
    def width(self) -> int:
        return self._tcl_call(int, "winfo", "width", self)

    @property
    @update_before
    def height(self) -> int:
        return self._tcl_call(int, "winfo", "height", self)

    def destroy(self):
        for child in self.child_stats.children:
            child.destroy()

        self._tcl_call(None, "destroy", self.tcl_path)
        del self.parent._children[self.tcl_path]



class TkWidget(MethodMixin):
    """Base class for every Tukaan widget"""

    def __init__(self):
        self._children: Dict[str, "TkWidget"] = {}
        self._child_type_count: Dict["TkWidget", int] = {}
        self.child_stats = ChildStatistics(self)

    @classmethod
    def _py_to_tcl_arguments(self, kwargs) -> tuple:
        result = []

        for key, value in kwargs.items():
            if value is None:
                continue

            if key.endswith("_"):
                key = key[:-1]

            if callable(value):
                value = create_command(value)

            result.extend([f"-{key}", value])

        return tuple(result)


class BaseWidget(TkWidget):
    def __init__(self, parent: Union[TkWidget, None], widget_name: str, **kwargs) -> None:
        TkWidget.__init__(self)

        self.parent = parent if parent else get_tcl_interp()
        self.tcl_path = self._give_me_a_name()
        self._tcl_call = get_tcl_interp().tcl_call

        self.state = StateSet(self)

        self.parent._children[self.tcl_path] = self

        self._tcl_call(
            None, widget_name, self.tcl_path, *self._py_to_tcl_arguments(kwargs)
        )

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
        name = type(self)

        # FIXME: more elegant way to count child types
        # itertools.count isn't good, because we need plain ints

        count = self.parent._child_type_count.get(name, 0) + 1
        self.parent._child_type_count[name] = count

        name = f"{self.parent.tcl_path}.{name.__name__.lower()}{count}"

        return name

    def pack(self, **kwargs) -> None:
        get_tcl_interp().tcl_call(
            None, "pack", self, *self._py_to_tcl_arguments(kwargs)
        )

    def grid(self, **kwargs) -> None:
        get_tcl_interp().tcl_call(
            None, "grid", self, *self._py_to_tcl_arguments(kwargs)
        )

    def place(self, **kwargs) -> None:
        get_tcl_interp().tcl_call(
            None, "place", self, *self._py_to_tcl_arguments(kwargs)
        )
