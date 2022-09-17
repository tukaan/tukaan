from __future__ import annotations

import contextlib
from collections.abc import Iterator

from tukaan._base import Container, TkWidget, WidgetBase
from tukaan._props import FocusableProp
from tukaan._tcl import Tcl
from tukaan.enums import Orientation
from tukaan.exceptions import TukaanTclError

from .frame import Frame


class Pane(Frame):
    _widget: SplitView

    def __init__(
        self,
        *,
        padding: int | tuple[int, ...] | None = None,
        tooltip: str | None = None,
        weight: int | None = None,
    ):
        Frame.__init__(self, self._widget, padding=padding, tooltip=tooltip)

        self._stored_options = {"weight": weight}
        self.append()

    def __repr__(self):
        return f"<tukaan.SplitView.Pane in {self.parent}; tcl_name={self._name}>"

    def append(self) -> None:
        if self in self._widget:
            self.move(-1)
            return None

        Tcl.call(None, self._widget, "add", self, *Tcl.to_tcl_args(**self._stored_options))
        self._widget.panes.append(self)

    def move(self, new_index: int) -> None:
        self._widget.panes.remove(self)
        self._widget.panes.insert(new_index, self)

        if new_index == -1:
            new_index = "end"  # type: ignore

        Tcl.call(None, self._widget, "insert", new_index, self)

    def remove(self) -> None:
        with contextlib.suppress(TukaanTclError):
            Tcl.call(None, self._widget, "forget", self)
        self._widget.panes.remove(self)

    @property
    def weight(self) -> int | None:
        if self in self._widget:
            return Tcl.call(int, self._widget, "pane", self, "-weight")
        else:
            return self._stored_options.get("weight", 0)

    @weight.setter
    def weight(self, value: int) -> None:
        if self in self._widget:
            Tcl.call(None, self._widget, "pane", self, "-weight", value)
        self._stored_options["weight"] = value


class SplitView(WidgetBase, Container):
    _tcl_class = "ttk::panedwindow"

    focusable = FocusableProp()

    def __init__(
        self,
        parent: TkWidget,
        orientation: Orientation | None = None,
        *,
        focusable: bool | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, takefocus=focusable, orient=orientation, tooltip=tooltip)

        self.Pane = Pane
        setattr(self.Pane, "_widget", self)

        self.panes = []
        self._orientation = orientation

    def __len__(self) -> int:
        return len(self.panes)

    def __iter__(self) -> Iterator[Pane]:
        return iter(self.panes)

    def __contains__(self, pane: Pane) -> bool:
        return pane in self.panes

    def __getitem__(self, index: int) -> Pane:
        return self.panes[index]

    def _repr_details(self):
        return f"contains {len(self)} panes"

    def lock_panes(self):
        Tcl.call(None, "bindtags", self, (self, ".", "all"))

    def unlock_panes(self):
        Tcl.call(None, "bindtags", self, (self, "TPanedwindow", ".", "all"))

    @property
    def orientation(self):  # read-only
        return self._orientation
