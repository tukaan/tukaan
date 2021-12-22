from __future__ import annotations

from typing import Callable, Optional

from ._base import Any, BaseWidget, TkWidget
from ._variables import String, _TclVariable


class RadioButton(BaseWidget):
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
        parent: Optional[TkWidget] = None,
        focusable: Optional[bool] = None,
        on_click: Optional[Callable] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
        underline: Optional[int] = None,
        value: Optional[Any] = None,
        variable: Optional[_TclVariable] = None,
        width: Optional[int] = None,
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

    def select(self):
        """Also invokes the on_click command"""
        self._tcl_call(None, self, "invoke")


class RadioGroup(BaseWidget):
    _tcl_class = "ttk::frame"
    _keys = {}

    def __init__(
        self, parent: Optional[TkWidget] = None, *, items: list[tuple[str, str]]
    ) -> None:
        BaseWidget.__init__(self, parent)
        self.variable = String(items[0][1])
        self.items = items

    def _repr_details(self) -> str:
        return f"number_of_items={len(self._items)}, selected={self.selected_item!r}"

    def select(self, value: str) -> None:
        self.variable.set(value)

    @property
    def value(self):
        return self.variable.get()

    @property
    def selected_item(self):
        for radio in self._items:
            if radio[1] == self.variable.get():
                return radio

    @property
    def items(self) -> list[tuple[str, str]]:
        return self._items

    @items.setter
    def items(self, new_items: list[tuple[str, str]]) -> None:
        self._items = new_items

        for item in self._tcl_call([str], "winfo", "children", self):
            self._tcl_call(None, "destroy", item)

        for index, item in enumerate(new_items):
            RadioButton(
                self, variable=self.variable, value=item[1], text=item[0]
            ).layout.grid(row=index)
