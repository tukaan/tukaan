from __future__ import annotations

from typing import Callable, Iterable, Optional

from ._base import BaseWidget, TkWidget
from ._misc import Color
from .entry import Entry
from .exceptions import TclError


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
        parent: Optional[TkWidget] = None,
        values: Optional[list | tuple] = None,
        *,
        current: Optional[int] = None,
        fg_color: Optional[str | Color] = None,
        focusable: Optional[bool] = None,
        hide_chars: Optional[bool] = False,
        hide_chars_with: Optional[str] = "•",
        on_click: Optional[Callable] = None,
        on_select: Optional[Callable] = None,
        style: Optional[str] = None,
        text_align: Optional[str] = None,
        user_edit: Optional[bool] = True,
        visible_rows: Optional[int] = None,
        width: Optional[int] = None,
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

        self.bind("<<ComboboxSelected>>", f"{self.tcl_path} selection clear")
        self.bind("<FocusOut>", f"+{self.tcl_path} selection clear")

        if on_select:
            self.bind("<<ComboboxSelected>>", on_select)

        if current is not None:
            self.current = current
        else:
            self.current = 0

    def __len__(self) -> int:
        return len(self._tcl_call([str], self, "cget", "-values"))

    def __iter__(self) -> Iterable[str]:
        return iter(self._tcl_call([str], self, "cget", "-values"))

    def __contains__(self, item: str) -> bool:
        return str(item) in self._tcl_call([str], self, "cget", "-values")

    def set(self, value: str) -> None:
        self._tcl_call(None, self, "set", value)

    value = property(Entry.get, set)

    @property
    def current(self) -> int:
        return self.values.index(self.get())

    @current.setter
    def current(self, index: int) -> None:
        try:
            self._tcl_call(None, self, "current", index)
        except TclError:
            raise IndexError("ComboBox index out of range")
