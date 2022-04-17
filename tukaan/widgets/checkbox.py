from __future__ import annotations

from typing import Callable

from tukaan._tcl import Tcl
from tukaan._variables import Boolean, _TclVariable

from ._base import BaseWidget, InputControlWidget, TkWidget


class CheckBox(BaseWidget, InputControlWidget):
    """To turn it on or off you have to use a control variable"""

    _tcl_class = "ttk::checkbutton"
    _keys = {
        "focusable": (bool, "takefocus"),
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: TkWidget,
        *,
        focusable: bool | None = None,
        on_click: Callable | None = None,
        style: str | None = None,
        text: str | None = None,
        underline: int | None = None,
        value: bool = False,
        variable: _TclVariable | None = None,
        width: int | None = None,
    ) -> None:
        if variable is None:
            self._variable = variable = Boolean(value)
        else:
            self._variable = variable

        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            offvalue=False,
            onvalue=True,
            style=style,
            takefocus=focusable,
            underline=underline,
            variable=variable,
            width=width,
        )
        self.config(text=text)

    def invoke(self):
        Tcl.call(None, self, "invoke")

    def select(self):
        self._variable.set(True)

    def deselect(self):
        self._variable.set(False)

    def toggle(self):
        self._variable.set(not self._variable.get())

    @property
    def is_selected(self) -> bool:
        return self._variable.get()

    @is_selected.setter
    def is_selected(self, is_selected: bool) -> None:
        self._variable.set(is_selected)

    value = is_selected  # for consistency with RadioButton
