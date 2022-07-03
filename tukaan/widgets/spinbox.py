from __future__ import annotations

from typing import Callable, Iterable

from tukaan._base import TkWidget, WidgetBase
from tukaan._props import cget, config
from tukaan._tcl import Tcl
from tukaan.colors import Color

from .textbox import TextBox


class SpinBox(TextBox):
    _tcl_class = "ttk::spinbox"

    def __init__(
        self,
        parent: TkWidget,
        values: Iterable[str | float] | range | None = None,
        *,
        cycle: bool | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        on_select: Callable[[str], None] | None = None,
        step: int | None = None,
        text_align: str | None = None,
        tooltip: str | None = None,
        user_edit: bool = True,
        value: str | float | None = None,
        width: int | None = None,
    ) -> None:
        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        self._original_cmd = on_select
        if on_select is not None:
            func = on_select
            on_select = lambda: func(self.get())  # type: ignore

        WidgetBase.__init__(
            self,
            parent,
            command=on_select,
            foreground=fg_color,
            justify=text_align,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            takefocus=focusable,
            tooltip=tooltip,
            width=width,
            wrap=cycle,
        )

        self._set_values(values, step)

        if value is not None:
            self.set(value)
        elif values:
            self.set(values[0])
        else:
            self.set("0")

        self.bind("<<Increment>>", f"+{self._name} selection clear")
        self.bind("<<Decrement>>", f"+{self._name} selection clear")
        self.bind("<FocusOut>", f"+{self._name} selection clear")

    def _set_values(self, values, arg_step) -> None:
        if isinstance(values, range):
            start, stop, step = values.start, values.stop, values.step
            if arg_step:
                step = arg_step

            return Tcl.call(
                None,
                self,
                "configure",
                *Tcl.to_tcl_args(from_=start, to=stop - step, increment=step),
            )

        Tcl.call(None, self, "configure", *Tcl.to_tcl_args(values=values))

    def set(self, value: str | float | None) -> None:
        Tcl.call(None, self, "set", value)

    value = property(TextBox.get, set)

    @property
    def values(self) -> list[str] | range:
        result = Tcl.call([str], self, "cget", "-values")

        if not result:
            start = Tcl.call(float, self, "cget", "-from") or 0
            stop = Tcl.call(float, self, "cget", "-to") or 0
            step = Tcl.call(float, self, "cget", "-increment")
            if isinstance(step, float):
                step = 1
            return range(start, stop, step)

        return result

    @values.setter
    def values(self, values: Iterable[str | float] | range | None) -> None:
        self._set_values(values, None)

    @property
    def cycle(self) -> bool:
        return cget(self, bool, "-wrap")

    @cycle.setter
    def cycle(self, value: bool) -> None:
        config(self, wrap=value)

    @property
    def step(self) -> float:
        return cget(self, float, "-increment")

    @step.setter
    def step(self, value: float) -> None:
        config(self, increment=value)

    @property
    def on_select(self) -> Callable[[str], None] | None:
        return self._original_cmd

    @on_select.setter
    def on_select(self, func: Callable[[str], None] | None) -> None:
        self._original_cmd = func
        if func is not None:
            value = lambda: func(self.get())
        else:
            value = ""
        config(self, command=value)
