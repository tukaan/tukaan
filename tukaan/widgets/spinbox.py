from __future__ import annotations

from typing import Callable

from tukaan._base import TkWidget, WidgetBase
from tukaan._props import BoolDesc, FloatDesc
from tukaan._tcl import Tcl
from tukaan.colors import Color

from .textbox import TextBox


class SpinBox(TextBox):
    _tcl_class = "ttk::spinbox"

    cycle = BoolDesc("wrap")
    max = FloatDesc("to")
    min = FloatDesc("from")
    step = FloatDesc("increment")

    def __init__(
        self,
        parent: TkWidget,
        min: float | None = None,
        max: float | None = None,
        step: float | None = None,
        *,
        cycle: bool | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        action: Callable[[str], None] | None = None,
        text_align: str | None = None,
        tooltip: str | None = None,
        user_edit: bool = True,
        value: float | None = None,
        width: int | None = None,
    ) -> None:
        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        self._action = action

        WidgetBase.__init__(
            self,
            parent,
            command=self._call_action,
            foreground=fg_color,
            from_=min,
            increment=step,
            justify=text_align,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            takefocus=focusable,
            to=max,
            tooltip=tooltip,
            width=width,
            wrap=cycle,
        )

        if value is not None:
            self.set(value)
        else:
            self.set(float(min or 0) if isinstance(step, float) else (min or 0))

        Tcl.call(None, "bind", self, "<<Increment>>", f"+{self._name} selection clear")
        Tcl.call(None, "bind", self, "<<Decrement>>", f"+{self._name} selection clear")
        Tcl.call(None, "bind", self, "<FocusOut>", f"+{self._name} selection clear")

    def _repr_details(self) -> str:
        return f"min={self.min!r}, max={self.max!r}, step={self.step!r}, value={self.value!r}"

    def _call_action(self) -> None:
        if self._action is not None:
            self._action(Tcl.call(float, self, "get"))

    @property
    def value(self) -> float:
        return Tcl.call(float, self, "get")

    @value.setter
    def value(self, value: float | None) -> None:
        Tcl.call(float, self, "set", value)

    @property
    def action(self) -> Callable[[str], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[str], None] | None) -> None:
        self._action = func
