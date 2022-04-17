from __future__ import annotations

from typing import Any, Callable

from tukaan._tcl import Tcl
from tukaan._variables import String, _TclVariable

from ._base import BaseWidget, InputControlWidget, TkWidget
from .frame import Frame


class RadioButton(BaseWidget, InputControlWidget):
    _tcl_class = "ttk::radiobutton"
    _keys = {
        "focusable": (bool, "takefocus"),
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "value": str,  # ???
        "variable": _TclVariable,
        "width": int,
    }

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        value: Any | None = None,
        variable: _TclVariable | None = None,
        *,
        focusable: bool | None = None,
        on_click: Callable | None = None,
        style: str | None = None,
        underline: int | None = None,
        width: int | None = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            style=style,
            takefocus=focusable,
            underline=underline,
            value=value,
            variable=variable,
            width=width,
        )
        self.config(text=text)

    def invoke(self):
        Tcl.call(None, self, "invoke")

    def select(self):
        self.variable.set(self.value)

    @property
    def is_selected(self) -> bool:  # read-only
        return self.variable.get() == self.value


class RadioGroup(Frame, InputControlWidget):
    _keys = {}

    def __init__(
        self,
        parent: TkWidget,
        items: dict[str, str],
        *,
        padding: int | tuple[int, ...] | None = None,
    ) -> None:
        Frame.__init__(self, parent, padding=padding)

        self.variable = String(tuple(items.keys())[0])
        self.items = items  # RadioGroup.items setter

    def _repr_details(self) -> str:
        item_id = self.variable.get()
        if item_id not in self._items:
            item_id = None

        return f"number of items={len(self._items)}, selected={item_id!r}"

    @property
    def value(self):
        return self.variable.get()

    def __getitem__(self, item: str) -> RadioButton:
        for radio in self.child_stats.children:
            if radio.item_id == item:
                return radio

        if item == self.variable.get():
            # selected getter wants to return a radio that no longer exists
            return None
        else:
            # user tries to select non-existent element
            raise RuntimeError(f"item with id {item!r} is not in this RadioGroup")

    @property
    def selected(self) -> RadioButton | None:
        return self[self.variable.get()]

    @selected.setter
    def selected(self, value: str) -> None:
        self.variable.set(value)

    @property
    def items(self) -> dict[str, str]:
        return self._items

    @items.setter
    def items(self, new_items: dict[str, str]) -> None:
        self._items = new_items

        for child in self.child_stats.children:
            child.destroy()

        for index, (id, text) in enumerate(tuple(new_items.items())):
            radio = RadioButton(self, variable=self.variable, value=id, text=text)
            radio.item_id = id
            radio.layout.grid(row=index)
