from __future__ import annotations

from collections.abc import Iterator

from tukaan._base import TkWidget, Widget
from tukaan._properties import FocusableProp, PaddingProp, StrDesc, cget
from tukaan._tcl import Tcl
from tukaan._typing import PaddingType
from tukaan.enums import Orientation


class Frame(Widget, widget_cmd="frame", tk_class="Frame"):
    def __init__(self, parent: TkWidget) -> None:
        Widget.__init__(self, parent)


class Panel(Widget, widget_cmd="ttk::frame", tk_class="TFrame"):
    padding = PaddingProp()

    def __init__(self, parent: TkWidget, *, padding: PaddingType = None) -> None:
        Widget.__init__(self, parent)

        self.padding = padding


class LabeledPanel(Widget, widget_cmd="ttk::labelframe", tk_class="TLabelframe"):
    padding = PaddingProp()
    text = StrDesc()

    def __init__(
        self, parent: TkWidget, text: str | None = None, *, padding: PaddingType = None
    ) -> None:
        Widget.__init__(self, parent, text=text)

        self.padding = padding


class Pane(Panel):
    parent: SplitView

    def __init__(
        self,
        owner: SplitView,
        *,
        padding: int | tuple[int, ...] | None = None,
        weight: int | None = None,
        auto_append: bool = True,
    ) -> None:
        super().__init__(owner, padding=padding)
        self._stored_options = {"weight": weight}

        if auto_append:
            self.append()

    def append(self) -> None:
        if self in self.parent:
            self.parent.panes.remove(self)
            self.parent.panes.append(self)

            Tcl.call(None, self.parent, "insert", "end", self)
            return

        Tcl.call(None, self.parent, "add", self, *Tcl.to_tcl_args(**self._stored_options))
        self.parent.panes.append(self)

    def move(self, new_index: int) -> None:
        if new_index < 0:
            raise ValueError("cannot use negative indices in pane.move()")

        self.parent.panes.remove(self)
        self.parent.panes.insert(new_index, self)

        Tcl.call(None, self.parent, "insert", new_index, self)

    def remove(self) -> None:
        if self in self.parent.panes:
            Tcl.call(None, self.parent, "forget", self)
            self.parent.panes.remove(self)

    @property
    def weight(self) -> int | None:
        if self in self.parent.panes:
            return Tcl.call(int, self.parent, "pane", self, "-weight")
        else:
            return self._stored_options.get("weight", 0)

    @weight.setter
    def weight(self, value: int) -> None:
        if self in self.parent.panes:
            Tcl.call(None, self.parent, "pane", self, "-weight", value or 0)
        self._stored_options["weight"] = value or 0


class SplitView(Widget, widget_cmd="ttk::panedwindow", tk_class="TPanedwindow"):
    focusable = FocusableProp()

    def __init__(
        self,
        parent: TkWidget,
        orientation: Orientation | None = None,
        *,
        focusable: bool | None = None,
    ) -> None:
        super().__init__(parent, takefocus=focusable, orient=orientation)

        self.panes = []

    def __len__(self) -> int:
        return len(self.panes)

    def __iter__(self) -> Iterator[Pane]:
        return iter(self.panes)

    def __contains__(self, pane: Pane) -> bool:
        return pane in self.panes

    def __getitem__(self, index: int) -> Pane:
        return self.panes[index]

    def create_pane(self, **kwargs) -> Pane:
        return Pane(self, **kwargs)

    def lock_panes(self):
        Tcl.call(None, "bindtags", self, (self, ".", "all"))

    def unlock_panes(self):
        Tcl.call(None, "bindtags", self, (self, self._tk_class, ".", "all"))

    @property
    def orientation(self):  # read-only
        return cget(self, Orientation, "-orient")


class TabView:
    ...
