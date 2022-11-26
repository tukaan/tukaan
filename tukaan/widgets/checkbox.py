from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import FocusableProp, LinkProp, TextProp, WidthProp
from tukaan._tcl import Tcl
from tukaan._variables import BoolVar


class CheckBox(WidgetBase, InputControl):
    _tcl_class = "ttk::checkbutton"
    _variable: BoolVar

    focusable = FocusableProp()
    target = LinkProp()
    text = TextProp()
    width = WidthProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str = None,
        *,
        action: Callable[[bool], None] | None = None,
        focusable: bool | None = None,
        selected: bool = False,
        target: BoolVar | None = None,
        tooltip: str | None = None,
        width: int | None = None,
    ) -> None:

        self._variable = BoolVar(selected) if target is None else target
        self._action = action

        WidgetBase.__init__(
            self,
            parent,
            command=self._call_action,
            offvalue=False,
            onvalue=True,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            variable=self._variable,
            width=width,
        )

    def _call_action(self) -> None:
        if self._action is not None:
            self._action(self._variable.get())

    def invoke(self) -> None:
        """Invoke the checkbox, as if it were clicked."""
        Tcl.call(None, self, "invoke")

    def select(self) -> None:
        """Select the checkbox."""
        self._variable.set(True)

    def deselect(self) -> None:
        """Deselect the checkbox."""
        self._variable.set(False)

    def toggle(self) -> None:
        """Toggle the state of the checkbox."""
        self._variable.set(not self._variable.get())

    @property
    def selected(self) -> bool:
        return self._variable.get()

    @selected.setter
    def selected(self, value: bool) -> None:
        self._variable.set(value)

    @property
    def action(self) -> Callable[[bool], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[bool], None] | None) -> None:
        self._action = func
