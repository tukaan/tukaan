from __future__ import annotations

from typing import Optional

from ._base import BaseWidget, TkWidget
from ._utils import py_to_tcl_args
from .frame import Frame
from .exceptions import TclError


class Pane(Frame):
    _keys = {"weight": int}

    def __init__(
        self,
        padding: Optional[int | tuple[int, ...]] = None,
        weight: Optional[int] = None,
    ):
        Frame.__init__(self, self._widget, padding=padding)

        self._store_options = {"weight": weight}

    def __repr__(self):
        return f"<tukaan.SplitView.Pane in {self.parent}; tcl_name={self.tcl_path}>"

    def _get(self, type_spec, key):
        if self in self._widget:
            return self._tcl_call(type_spec, self._widget, "pane", self, f"-{key}")
        else:
            return self._store_options.get(key, None)

    def _set(self, **kwargs):
        if self in self._widget:
            self._tcl_call(None, self._widget, "pane", self, *py_to_tcl_args(**kwargs))
        else:
            self._store_options.update(kwargs)

    def append(self):
        if self in self._widget:
            self.move(-1)
            return
        
        self._tcl_call(None, self._widget, "add", self, *py_to_tcl_args(**self._store_options))
        self._widget.panes.append(self)

    def move(self, new_index: int) -> None:
        self._widget.panes.remove(self)
        self._widget.panes.insert(new_index, self)

        if new_index == -1:
            new_index = "end"

        self._tcl_call(None, self._widget, "insert", new_index, self)

    def remove(self):
        try:
            self._tcl_call(None, self._widget, "forget", self)
        except TclError:  # Pane isn't added to SplitView
            pass


class SplitView(BaseWidget):
    _tcl_class = "ttk::panedwindow"
    _keys = {
        "focusable": (bool, "takefocus"),
    }

    def __init__(self, parent: Optional[TkWidget] = None, focusable: Optional[bool] = None, orientation: Optional[str] = None) -> None:
        BaseWidget.__init__(self, parent, takefocus=focusable, orient=orientation)

        self.Pane = Pane
        setattr(self.Pane, "_widget", self)

        self.panes = []
        self._orientation = orientation

    def __contains__(self, pane):
        return pane in self.panes

    def __iter__(self):
        return iter(self.panes)

    def __len__(self):
        return len(self.panes)

    def _repr_details(self):
        return f"contains {len(self)} panes"

    def __getitem__(self, index):
        if isinstance(index, self.Pane):
            return self.panes.index(index)

        return self.panes[index]

    @property
    def orientation(self):  # orientation is read-only
        return self._orientation

    def lock_panes(self):
        self._tcl_call(None, "bindtags", self, (self, ".", "all"))

    def unlock_panes(self):
        self._tcl_call(None, "bindtags", self, (self, "TPanedwindow", ".", "all"))
