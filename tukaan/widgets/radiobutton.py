from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import (
    CommandProp,
    FocusableProp,
    IntDesc,
    LinkProp,
    TextProp,
    WidthProp,
    cget,
    config,
)
from tukaan._tcl import Tcl
from tukaan._variables import ControlVariable, String
from tukaan.enums import Orientation

from .frame import Frame


class RadioButton(WidgetBase, InputControl):
    _tcl_class = "ttk::radiobutton"

    focusable = FocusableProp()
    link = LinkProp()
    on_click = CommandProp()
    text = TextProp()
    width = WidthProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str,
        value: str | float | bool,
        link: ControlVariable,
        *,
        focusable: bool | None = None,
        on_click: Callable[..., None] | None = None,
        tooltip: str | None = None,
        width: int | None = None,
    ) -> None:
        self._variable = link
        self._value_type = type(value)

        WidgetBase.__init__(
            self,
            parent,
            command=on_click,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            value=value,
            variable=link,
            width=width,
        )

    def invoke(self):
        """Invoke the radiobutton, as if it were clicked."""
        Tcl.call(None, self, "invoke")

    def select(self):
        """Select the radiobutton."""
        self._variable.set(self.value)

    @property
    def selected(self) -> bool:
        """Return whether the radiobutton is selected or not."""
        return self._variable.get() == self.value

    ### Properties ###

    @property
    def value(self) -> str | float | bool:
        return cget(self, self._value_type, "-value")

    @value.setter
    def value(self, value: str | float | bool) -> None:
        self._value_type = type(value)
        config(self, value=value)


class RadioGroup(Frame, InputControl):
    _items: dict[str, RadioButton]

    def __init__(
        self,
        parent: TkWidget,
        items: dict[str, str],
        *,
        selected: str | None = None,
        orientation: Orientation = Orientation.Vertical,
        padding: int | tuple[int, ...] | None = None,
    ) -> None:
        self._items = {}

        Frame.__init__(self, parent, padding=padding)

        self.link = String(selected or tuple(items.keys())[0])
        self._orient = orientation
        self._set_items(items)

    def _repr_details(self) -> str:
        item_id = self.link.get()
        if item_id not in self._items:
            item_id = None

        return f"number of items={len(self._items)}, selected={item_id!r}"

    def _set_items(self, items: dict[str, str]) -> None:
        for (value, text) in items.items():
            radio = RadioButton(self, text, value, self.link)
            self._items[value] = radio
        self._regrid()

    def _regrid(self):
        is_vert = self._orient is Orientation.Vertical
        for index, radio in enumerate(self._items.values()):
            if is_vert:
                Tcl.call(None, "grid", radio, "-row", index, "-column", 0, "-sticky", "w")
            else:
                Tcl.call(None, "grid", radio, "-row", 0, "-column", index)

    def __getitem__(self, item: str) -> RadioButton | None:
        return self._items.get(item)

    def append(self, value: str, text: str) -> None:
        radio = RadioButton(self, text, value, self.link)
        self._items[value] = radio
        self._regrid()

    def remove(self, item: str) -> None:
        self._items[item].destroy()

    @property
    def value(self) -> str:
        return self.link.get()

    @value.setter
    def value(self, value: str) -> None:
        self.link.set(value)

    @property
    def selected(self) -> RadioButton | None:
        return self._items.get(self.link.get())

    @selected.setter
    def selected(self, value: str) -> None:
        self.link.set(value)

    @property
    def orientation(self) -> Orientation:
        return self._orient

    @orientation.setter
    def orientation(self, value: str) -> None:
        self._orient = value
        self._regrid()
