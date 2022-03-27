from __future__ import annotations

from typing import Callable, Optional

from ._base import BaseWidget, TkWidget
from tukaan._enums import ImagePosition
from tukaan._helpers import convert_4side, convert_4side_back
from tukaan._images import Icon, Image, _image_converter_class
from tukaan._tcl import Tcl
from tukaan.exceptions import TclError
from .frame import Frame


class Tab(Frame):
    _keys = {
        "icon": (_image_converter_class, "image"),
        "image_pos": (ImagePosition, "compound"),
        "title": (str, "text"),
        "underline": int,
    }

    def __init__(
        self,
        title: Optional[str] = None,
        *,
        icon: Optional[Icon | Image] = None,
        image_pos: ImagePosition = ImagePosition.Left,
        margin: Optional[int | tuple[int, ...]] = None,
        padding: Optional[int | tuple[int, ...]] = None,
        underline: Optional[int] = None,
    ):
        Frame.__init__(self, self._widget, padding=padding)

        self._store_options = {
            "compound": image_pos,
            "image": icon,
            "text": title,
            "underline": underline,
            "padding": convert_4side(margin),
        }
        self.append()

    def __repr__(self):
        return f"<tukaan.TabView.Tab in {self.parent}; tcl_name={self.tcl_path}>"

    def _get(self, type_spec, key):
        if key == "margin":
            return self.margin

        if self in self._widget:
            return self._tcl_call(type_spec, self._widget, "tab", self, f"-{key}")
        else:
            return self._store_options.get(key, None)

    def _set(self, **kwargs):
        if "margin" in kwargs:
            self.margin = kwargs.pop("margin", (0,) * 4)

        if self in self._widget:
            self._tcl_call(None, self._widget, "tab", self, *Tcl.to_tcl_args(**kwargs))
        else:
            self._store_options.update(kwargs)

    @property
    def margin(self):
        return convert_4side_back(
            tuple(map(int, self._tcl_call((str,), self._widget, "tab", self, "-padding")))
        )

    @margin.setter
    def margin(self, new_margin):
        self._tcl_call(None, self._widget, "tab", self, "-padding", convert_4side(new_margin))

    def select(self):
        if self not in self._widget:
            self.append()

        self._tcl_call(None, self._widget, "select", self)

    def append(self):
        if self in self._widget:
            self.move(-1)
            return

        self._tcl_call(None, self._widget, "add", self, *Tcl.to_tcl_args(**self._store_options))
        self._widget.tabs.append(self)

    def move(self, new_index: int) -> None:
        self._widget.tabs.remove(self)
        self._widget.tabs.insert(new_index, self)

        if new_index == -1:
            new_index = "end"

        self._tcl_call(None, self._widget, "insert", new_index, self)

    def hide(self):
        self._tcl_call(None, self._widget, "hide", self)

    def unhide(self):
        self._tcl_call(None, self._widget, "add", self)

    def remove(self):
        try:
            self._tcl_call(None, self._widget, "forget", self)
        except TclError:  # Tab isn't added to TabView
            pass

    @property
    def enabled(self):
        return self._get(str, "state") == "normal"

    @enabled.setter
    def enabled(self, is_enabled: bool):
        return self._set(state="normal" if is_enabled else "disabled")


class TabView(BaseWidget):
    _tcl_class = "ttk::notebook"
    _keys = {
        "focusable": (bool, "takefocus"),
    }

    def __init__(self, parent: Optional[TkWidget] = None, focusable: Optional[bool] = None) -> None:
        BaseWidget.__init__(self, parent, takefocus=focusable)

        self.Tab = Tab
        setattr(self.Tab, "_widget", self)

        self.tabs = []

    def __contains__(self, tab):
        return tab in self.tabs

    def __iter__(self):
        return iter(self.tabs)

    def __len__(self):
        return len(self.tabs)

    def _repr_details(self):
        return f"contains {len(self)} tabs"

    def __getitem__(self, index):
        if isinstance(index, self.Tab):
            return self.tabs.index(index)

        return self.tabs[index]

    @property
    def selected(self):
        try:
            selected = self._tcl_eval(int, f"{self.tcl_path} index [{self.tcl_path} select]")
        except TclError:
            return None

        return self.tabs[selected]

    @selected.setter
    def selected(self, tab: Tab):
        tab.select()

    def on_tab_change(self, func: Callable[[Tab], None]) -> Callable[[Tab], None]:
        def wrapper() -> None:
            func(self.selected)

        self.events.bind("<<NotebookTabChanged>>", wrapper)
        return wrapper

    def enable_keyboard_traversal(self):
        self._tcl_call(None, "ttk::notebook::enableTraversal", self)

    def enable_tab_dragging(self):
        self.events.bind("<Button1-Motion>", self._on_tab_drag, send_event=True)

    def _on_tab_drag(self, event):
        x, y = event.x, event.y

        if self._tcl_call(str, self, "identify", x, y) == "Notebook.tab":
            # when the tab has a big image, 'Notebook.tab' glitches only at first tab, 'label' everywhere
            self._tcl_eval(
                None,
                f"{self.tcl_path} insert [{self.tcl_path} index @{x},{y}] [{self.tcl_path} select]",
            )
            return False  # like 'break' in tkinter
