from __future__ import annotations

from typing import Callable, Iterable

from tukaan._base import TkWidget, WidgetBase
from tukaan._props import cget, config
from tukaan._tcl import Tcl
from tukaan._utils import _commands
from tukaan.colors import Color
from tukaan.exceptions import TclError

from .textbox import TextBox


class ComboBox(TextBox):
    _tcl_class = "ttk::combobox"

    def __init__(
        self,
        parent: TkWidget,
        values: list[str | float] | None = None,
        *,
        current: int | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        on_click: Callable | None = None,
        on_select: Callable | None = None,
        text_align: str | None = None,
        tooltip: str | None = None,
        user_edit: bool | None = True,
        visible_rows: int | None = None,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        WidgetBase.__init__(
            self,
            parent,
            foreground=fg_color,
            height=visible_rows,
            justify=text_align,
            postcommand=on_click,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            takefocus=focusable,
            tooltip=tooltip,
            values=values,
            width=width,
        )

        self.bind("<<ComboboxSelected>>", f"+{self._name} selection clear")
        self.bind("<FocusOut>", f"+{self._name} selection clear")

        if on_select:
            self.bind("<<ComboboxSelected>>", on_select)

        if values:
            self.current = 0 if current is None else current

    def __len__(self) -> int:
        return len(Tcl.call([str], self, "cget", "-values"))

    def __iter__(self) -> Iterable[str]:
        return iter(Tcl.call([str], self, "cget", "-values"))

    def __contains__(self, item: str) -> bool:
        return item in Tcl.call([str], self, "cget", "-values")

    def set(self, value: str) -> None:
        Tcl.call(None, self, "set", value)

    value = property(TextBox.get, set)

    # Properties #

    @property
    def current(self) -> int:
        return self.values.index(self.get())

    @current.setter
    def current(self, index: int) -> None:
        try:
            Tcl.call(None, self, "current", index)
        except TclError:
            raise IndexError("ComboBox index out of range") from None

    @property
    def visible_rows(self) -> int:
        return cget(self, int, "-height")

    @visible_rows.setter
    def visible_rows(self, value: int) -> None:
        config(self, height=value)

    @property
    def values(self) -> list[str]:
        return cget(self, [str], "-values")

    @values.setter
    def values(self, value: list[str | float] | None) -> None:
        if value is None:
            value = []
        config(self, values=value)

    @property
    def on_click(self) -> Callable[..., None] | None:
        return _commands.get(cget(self, str, "-postcommand"))

    @on_click.setter
    def on_click(self, func: Callable[..., None] | None) -> None:
        value = func
        if value is None:
            value = ""
        config(self, postcommand=value)
