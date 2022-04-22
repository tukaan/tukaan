from __future__ import annotations

from collections import namedtuple
from typing import Callable

from tukaan._tcl import Tcl
from tukaan.colors import Color

from ._base import BaseWidget, TkWidget
from .entry import Entry

SpinBox_values = namedtuple("SpinBox_values", ["start", "stop", "step"])


class SpinBox(Entry):
    _tcl_class = "ttk::spinbox"
    _keys = {
        "cycle": (bool, "wrap"),
        "fg_color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "hide_chars_with": (str, "show"),
        "increment": float,
        "max": (float, "to"),
        "min": (float, "from"),
        "on_xscroll": ("func", "xscrollcommand"),
        "style": str,
        "text_align": (str, "justify"),
        "width": int,
    }

    def __init__(
        self,
        parent: TkWidget,
        values: list[str | float] | tuple[str | float, ...] | range | None = None,
        *,
        cycle: bool | None = None,
        value: str | float | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        increment: int | None = None,
        max: int | None = None,
        min: int | None = None,
        on_select: Callable | None = None,
        style: str | None = None,
        text_align: str | None = None,
        user_edit: bool = True,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        BaseWidget.__init__(
            self,
            parent,
            foreground=fg_color,
            justify=text_align,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            style=style,
            takefocus=focusable,
            width=width,
            wrap=cycle,
        )

        self._set_values(values, min, max, increment)

        if value is not None:
            self.set(value)
        elif min:
            self.set(min)
        elif values:
            self.set(values[0])
        else:
            self.set("0")

        self.bind("<<Increment>>", f"+{self._name} selection clear")
        self.bind("<<Decrement>>", f"+{self._name} selection clear")
        self.bind("<FocusOut>", f"+{self._name} selection clear")

    def set(self, value: str) -> None:
        Tcl.call(None, self, "set", value)

    value = property(Entry.get, set)

    @property
    def values(self) -> list[str | float]:
        result = Tcl.call([str], self, "cget", "-values")

        if not result:
            min_ = Tcl.call(float, self, "cget", "-from") or 0
            max_ = Tcl.call(float, self, "cget", "-to") or 0
            increment = Tcl.call(float, self, "cget", "-increment") or 1
            return SpinBox_values(min_, max_ + increment, increment)

        return result

    @values.setter
    def values(self, values: list[str | float]) -> None:
        self._set_values(values)

    def _set_values(
        self,
        values: list[str | float] | tuple[str | float, ...] | range = None,
        min_: int = None,
        max_: int = None,
        increment: int = None,
    ) -> None:
        if isinstance(values, range):
            if min_ is None:
                min_ = values.start
            if max_ is None:
                max_ = values.stop
            if increment is None:
                increment = values.step
        elif values is None and max_:
            if min_ is None:
                min_ = 0
            if max_ is None:
                max_ = 0
            if increment is None:
                increment = 1
        else:
            return self.config(values=values)

        Tcl.call(
            None,
            self._name,
            "configure",
            *Tcl.to_tcl_args(from_=min_, to=max_ - increment, increment=increment),
        )
