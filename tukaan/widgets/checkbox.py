from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import config, focusable, link, text, width
from tukaan._tcl import Tcl
from tukaan._variables import Boolean


class CheckBox(WidgetBase, InputControl):
    _tcl_class = "ttk::checkbutton"

    _variable: Boolean

    focusable = focusable
    link = link
    text = text
    width = width

    def __init__(
        self,
        parent: TkWidget,
        text: str,
        *,
        focusable: bool | None = None,
        link: Boolean | None = None,
        on_click: Callable[[bool], None] | None = None,
        tooltip: str | None = None,
        value: bool = False,
        width: int | None = None,
    ) -> None:

        if link is None:
            self._variable = link = Boolean(value)
        else:
            self._variable = link

        self._original_cmd = on_click
        if on_click is not None:
            func = on_click
            on_click = lambda: func(self._variable.get())  # type: ignore

        WidgetBase.__init__(
            self,
            parent,
            command=on_click,
            offvalue=False,
            onvalue=True,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            variable=link,
            width=width,
        )

    def invoke(self) -> None:
        """Invokes the checkbox, as if it were clicked"""

        Tcl.call(None, self, "invoke")

    def select(self) -> bool:
        """Selects the checkbox"""

        return self._variable.set(True)

    def deselect(self) -> bool:
        """Deselects the checkbox"""

        return self._variable.set(False)

    def toggle(self) -> bool:
        """Toggles the state of the checkbox"""

        return ~self._variable.set()

    @property
    def value(self) -> bool:
        return self._variable.get()

    @value.setter
    def value(self, value: bool) -> None:
        self._variable.set(value)

    selected = value

    @property
    def on_click(self) -> Callable[[bool], None] | None:
        return self._original_cmd

    @on_click.setter
    def on_click(self, func: Callable[[bool], None] | None) -> None:
        self._original_cmd = func
        if func is not None:
            value = lambda: func(self._variable.get())
        else:
            value = ""
        config(self, command=value)
