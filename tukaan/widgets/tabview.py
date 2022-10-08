from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Callable

from PIL import Image

from tukaan._base import Container, TkWidget, WidgetBase
from tukaan._images import Icon, Pillow2Tcl
from tukaan._props import FocusableProp, _convert_padding, _convert_padding_back
from tukaan._tcl import Tcl
from tukaan.enums import ImagePosition
from tukaan.exceptions import TukaanTclError

from .frame import Frame


class Tab(Frame):
    _widget: TabView

    def __init__(
        self,
        title: str | None = None,
        *,
        icon: Icon | Image.Image | None = None,
        image_pos: ImagePosition = ImagePosition.Left,
        margin: int | tuple[int, ...] | None = None,
        padding: int | tuple[int, ...] | None = None,
        tooltip: str | None = None,
    ):
        Frame.__init__(self, self._widget, padding=padding, tooltip=tooltip)

        self._stored_options = {
            "compound": image_pos,
            "image": icon,
            "padding": _convert_padding(margin),
            "text": title,
        }
        self.append()

    def __repr__(self):
        return f"<TabView.Tab in {self.parent}; tcl_name={self._name}>"

    def select(self) -> None:
        if self not in self._widget:
            self.append()

        Tcl.call(None, self._widget, "select", self)

    def append(self) -> None:
        if self in self._widget:
            self.move(-1)
            return None

        Tcl.call(None, self._widget, "add", self, *Tcl.to_tcl_args(**self._stored_options))
        self._widget.tabs.append(self)

    def move(self, new_index: int) -> None:
        self._widget.tabs.remove(self)
        self._widget.tabs.insert(new_index, self)

        if new_index == -1:
            new_index = "end"  # type: ignore

        Tcl.call(None, self._widget, "insert", new_index, self)

    def hide(self) -> None:
        Tcl.call(None, self._widget, "hide", self)

    def unhide(self) -> None:
        Tcl.call(None, self._widget, "add", self)

    def remove(self) -> None:
        with contextlib.suppress(TukaanTclError):
            Tcl.call(None, self._widget, "forget", self)
        self._widget.tabs.remove(self)

    @property
    def enabled(self) -> bool:
        return self._get(str, "state") == "normal"

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._set(state="normal" if value else "disabled")

    @property
    def title(self) -> str | None:
        if self in self._widget:
            return Tcl.call(str, self._widget, "tab", self, "-text")
        else:
            return self._stored_options.get("text")

    @title.setter
    def title(self, value: str) -> None:
        if self in self._widget:
            Tcl.call(None, self._widget, "tab", self, "-text", value)
        self._stored_options["text"] = value

    @property
    def icon(self) -> Icon | Image.Image | None:
        if self in self._widget:
            return Tcl.call(Pillow2Tcl, self._widget, "tab", self, "-image")
        else:
            return self._stored_options.get("image")

    @icon.setter
    def icon(self, value: Icon | Image.Image) -> None:
        if self in self._widget:
            Tcl.call(None, self._widget, "tab", self, "-image", value)
        self._stored_options["image"] = value

    @property
    def image_pos(self) -> str | None:
        if self in self._widget:
            return Tcl.call(str, self._widget, "tab", self, "-compound")
        else:
            return self._stored_options.get("compound")

    @image_pos.setter
    def image_pos(self, value: str) -> None:
        if self in self._widget:
            Tcl.call(None, self._widget, "tab", self, "-compound", value)
        self._stored_options["compound"] = value

    @property
    def margin(self) -> tuple[int, int, int, int] | None:
        if self in self._widget:
            result = Tcl.call(str, self._widget, "tab", self, "-padding")
        else:
            result = self._stored_options.get("padding")

        return _convert_padding_back(result)

    @margin.setter
    def margin(self, value: int | tuple[int, ...] | None) -> None:
        converted = _convert_padding(value)

        if self in self._widget:
            Tcl.call(None, self._widget, "tab", self, "-padding", converted)
        self._stored_options["padding"] = converted


class TabView(WidgetBase, Container):
    _tcl_class = "ttk::notebook"

    focusable = FocusableProp()

    def __init__(
        self,
        parent: TkWidget,
        *,
        focusable: bool | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, takefocus=focusable, tooltip=tooltip)

        self.Tab = Tab
        setattr(self.Tab, "_widget", self)

        self.tabs = []

    def __len__(self) -> int:
        return len(self.tabs)

    def __iter__(self) -> Iterator[Tab]:
        return iter(self.tabs)

    def __contains__(self, tab: Tab) -> bool:
        return tab in self.tabs

    def __getitem__(self, index: int) -> Tab:
        return self.tabs[index]

    def _repr_details(self) -> str:
        return f"contains {len(self)} tabs"

    def index(self, tab: Tab) -> int:
        return self.tabs.index(tab)

    @property
    def selected(self) -> Tab | None:
        try:
            selected = Tcl.eval(int, f"{self._name} index [{self._name} select]")
        except TukaanTclError:
            return None
        else:
            return self.tabs[selected]

    @selected.setter
    def selected(self, tab: Tab) -> None:
        tab.select()

    def on_tab_change(self, func: Callable[[Tab | None], None]) -> Callable[[], None]:
        def wrapper() -> None:
            func(self.selected)

        self.events.bind("<<NotebookTabChanged>>", wrapper)
        return wrapper

    def enable_keyboard_traversal(self) -> None:
        Tcl.call(None, "ttk::notebook::enableTraversal", self)

    def enable_tab_dragging(self) -> None:
        self.events.bind("<Button1-Motion>", self._on_tab_drag, send_event=True)

    def _on_tab_drag(self, event) -> bool | None:
        x, y = event.x, event.y

        if Tcl.call(str, self, "identify", x, y) == "Notebook.tab":
            # I'm using 'Notebook.tab' here, 'coz when the tab has a big image,
            # 'Notebook.tab' glitches only at first tab, 'label' everywhere
            Tcl.eval(
                None,
                f"{self._name} insert [{self._name} index @{x},{y}] [{self._name} select]",
            )
            return False  # like 'break' in tkinter
