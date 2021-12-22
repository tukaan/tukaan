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

    def invoke(self):
        self._tcl_call(None, self, "invoke")

    def select(self):
        self.variable.set(self.value)

    @property
    def is_selected(self) -> bool:
        return self.variable.get() == self.value

    @is_selected.setter
    def is_selected(self, _: bool) -> bool:
        raise AttributeError("RadioButton.is_selected is read-only")


class RadioGroup(BaseWidget):
    _tcl_class = "ttk::frame"
    _keys: dict[str, Any | tuple[Any, str]] = {}

    def __init__(
        self, parent: Optional[TkWidget] = None, *, items: list[tuple[str, str]]
    ) -> None:
        BaseWidget.__init__(self, parent)
        self.variable = String(items[0][1])
        self.items = items

    def _repr_details(self) -> str:
        return f"number_of_items={len(self._items)}, selected={self.selected_item!r}"

    @property
    def value(self):
        return self.variable.get()

    def get_item(self, item: str) -> BaseWidget:
        for radio in self.child_stats.children:
            if radio.item_id == item:
                return radio
        raise RuntimeError(f"item with id {item!r} is not in this RadioGroup")

    def destroy_item(self, item: str) -> None:
        for radio in self.child_stats.children:
            if radio.item_id == item:
                radio.destroy()
        raise RuntimeError(f"item with id {item!r} is not in this RadioGroup")

    @property
    def selected_item(self) -> BaseWidget | None:
        value = self.variable.get()
        for radio in self._items:
            if radio[1] == value:
                return self.get_item(radio[1])
        return None

    @selected_item.setter
    def selected_item(self, value: str) -> None:
        self.variable.set(value)

    @property
    def items(self) -> list[tuple[str, str]]:
        return self._items

    @items.setter
    def items(self, new_items: list[tuple[str, str]]) -> None:
        self._items = new_items

        for child in self.child_stats.children:
            child.destroy()

        for index, item in enumerate(new_items):
            radio = RadioButton(
                self, variable=self.variable, value=item[1], text=item[0]
            )
            radio.item_id = item[1]
            radio.layout.grid(row=index)
