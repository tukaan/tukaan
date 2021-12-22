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

        for index, item in enumerate(items):
            RadioButton(
                self, variable=self.variable, value=item[1], text=item[0]
            ).layout.grid(row=index)

    def select(self, value: str) -> None:
        self.variable.set(value)

    @property
    def value(self):
        return self.variable.get()
