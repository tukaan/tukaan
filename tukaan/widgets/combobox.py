from __future__ import annotations

from typing import Callable, Iterable

from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.exceptions import TclError

from ._base import BaseWidget, TkWidget
from .entry import Entry


class ComboBox(Entry):
    _tcl_class = "ttk::combobox"
    _keys = {
        "fg_color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "hide_chars_with": (str, "show"),
        "on_click": ("func", "postcommand"),
        "on_xscroll": ("func", "xscrollcommand"),
        "style": str,
        "text_align": (str, "justify"),
        "values": [str],
        "visible_rows": (int, "height"),
        "width": int,
    }

    def __init__(
        self,
        parent: TkWidget,
        values: list | tuple | None = None,
        *,
        current: int | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        on_click: Callable | None = None,
        on_select: Callable | None = None,
        style: str | None = None,
        text_align: str | None = None,
        user_edit: bool | None = True,
        visible_rows: int | None = None,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        BaseWidget.__init__(
            self,
            parent,
            foreground=fg_color,
            height=visible_rows,
            justify=text_align,
            postcommand=on_click,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            style=style,
            takefocus=focusable,
            values=values,
            width=width,
        )

        self.bind("<<ComboboxSelected>>", f"{self._name} selection clear")
        self.bind("<FocusOut>", f"+{self._name} selection clear")

        if on_select:
            self.bind("<<ComboboxSelected>>", on_select)

        if current is not None:
            self.current = current
        else:
            self.current = 0

    def __len__(self) -> int:
        return len(Tcl.call([str], self, "cget", "-values"))

    def __iter__(self) -> Iterable[str]:
        return iter(Tcl.call([str], self, "cget", "-values"))

    def __contains__(self, item: str) -> bool:
        return str(item) in Tcl.call([str], self, "cget", "-values")

    def set(self, value: str) -> None:
        Tcl.call(None, self, "set", value)

    value = property(Entry.get, set)

    @property
    def current(self) -> int:
        return self.values.index(self.get())

    @current.setter
    def current(self, index: int) -> None:
        try:
            Tcl.call(None, self, "current", index)
        except TclError:
            raise IndexError("ComboBox index out of range")
