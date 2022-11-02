from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import FocusableProp, LinkProp, TextProp, WidthProp, config
from tukaan._tcl import Tcl
from tukaan._variables import Boolean


class CheckBox(WidgetBase, InputControl):
    _tcl_class = "ttk::checkbutton"

    _variable: Boolean

    focusable = FocusableProp()
    link = LinkProp()
    text = TextProp()
    width = WidthProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str = None,
        *,
        focusable: bool | None = None,
        link: Boolean | None = None,
        action: Callable[[bool], None] | None = None,  # FIXME: this can't be modified?
        tooltip: str | None = None,
        value: bool = False,
        width: int | None = None,
    ) -> None:

        if link is None:
            self._variable = link = Boolean(value)
        else:
            self._variable = link

        self._original_cmd = action
        if action is not None:
            func = action
            action = lambda: func(self._variable.get())  # type: ignore

        WidgetBase.__init__(
            self,
            parent,
            command=action,
            offvalue=False,
            onvalue=True,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            variable=link,
            width=width,
        )

    def invoke(self) -> None:
        """Invoke the checkbox, as if it were clicked."""
        Tcl.call(None, self, "invoke")

    def select(self) -> bool:
        """Select the checkbox."""
        return self._variable.set(True)

    def deselect(self) -> bool:
        """Deselect the checkbox."""
        return self._variable.set(False)

    def toggle(self) -> bool:
        """Toggle the state of the checkbox."""
        return ~self._variable.set()  # FIXME: wut?? This doesn't seem right

    @property
    def value(self) -> bool:
        return self._variable.get()

    @value.setter
    def value(self, value: bool) -> None:
        self._variable.set(value)

    selected = value

    @property
    def action(self) -> Callable[[bool], None] | None:
        return self._original_cmd

    @action.setter
    def action(self, func: Callable[[bool], None] | None) -> None:
        self._original_cmd = func
        if func is not None:
            value = lambda: func(self._variable.get())
        else:
            value = ""
        config(self, command=value)
