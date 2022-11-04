from __future__ import annotations

from typing import Callable, Iterable

from tukaan._base import TkWidget, WidgetBase
from tukaan._collect import _commands
from tukaan._props import cget, config
from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.exceptions import TukaanTclError

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
        action: Callable | None = None,
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
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            takefocus=focusable,
            tooltip=tooltip,
            values=values,
            width=width,
        )

        self._action = action

        self.bind("<FocusOut>", f"+{self._name} selection clear")
        self.bind("<<ComboboxSelected>>", self._call_action)

        if values:
            self.current = 0 if current is None else current

    def __len__(self) -> int:
        return len(Tcl.call([str], self, "cget", "-values"))

    def __iter__(self) -> Iterable[str]:
        return iter(Tcl.call([str], self, "cget", "-values"))

    def __contains__(self, item: str) -> bool:
        return item in Tcl.call([str], self, "cget", "-values")

    def _call_action(self) -> None:
        Tcl.call(None, self, "selection", "clear")
        if self._action is not None:
            self._action(self.get())

    def set(self, value: str) -> None:
        Tcl.call(None, self, "set", value)

    value = property(TextBox.get, set)

    @property
    def current(self) -> int:
        try:
            result = self.values.index(self.get())
        except ValueError:
            result = None
        finally:
            return result

    @current.setter
    def current(self, index: int) -> None:
        try:
            Tcl.call(None, self, "current", index)
        except TukaanTclError:
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
    def action(self) -> Callable[[str], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[str], None] | None) -> None:
        self._action = func
