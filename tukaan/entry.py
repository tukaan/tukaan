from __future__ import annotations

import warnings
from typing import Literal, Optional

from ._base import BaseWidget, TkWidget
from ._misc import Color

EndAlias = Literal["end"]


class Entry(BaseWidget):
    _keys = {
        "color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "hide_chars_with": (str, "show"),
        "justify": str,
        "style": str,
    }

    start = 0
    end = "end"

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        color: Optional[str | Color] = None,
        focusable: Optional[bool] = None,
        hide_chars: bool = False,
        hide_chars_with: Optional[str] = "•",
        justify: Optional[Literal["center", "left", "right"]] = None,
        style: Optional[str] = None,
        width: Optional[int] = None,
    ) -> None:
        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        BaseWidget.__init__(
            self,
            parent,
            "ttk::entry",
            foreground=color,
            justify=justify,
            show=hide_chars_with,
            style=style,
            takefocus=focusable,
            width=width,
        )

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __contains__(self, text: str):
        return text in self.get()

    def _repr_details(self) -> str:
        value = self.value
        return f"value='{value if len(value) <= 10 else value[:10] + '...'}'"

    def clear(self) -> None:
        self._tcl_call(None, self, "delete", 0, "end")

    def delete(self, start: int | EndAlias, end: int | EndAlias = "end") -> None:
        self._tcl_call(None, self, "delete", start, end)

    def get(self) -> str:
        return self._tcl_call(str, self, "get")

    def insert(self, index: int | EndAlias, text: str) -> None:
        self._tcl_call(None, self, "insert", index, text)

    @property
    def cursor_pos(self):
        return self._tcl_call(int, self, "index", "insert")

    @cursor_pos.setter
    def cursor_pos(self, new_pos):
        self._tcl_call(None, self, "icursor", new_pos)

    @property
    def value(self) -> str:
        return self.get()

    @value.setter
    def value(self, new_value: str) -> None:
        self.clear()
        self.insert(0, new_value)

    @property
    def hide_chars(self) -> bool:
        return self.hide_chars_with != ""

    @hide_chars.setter
    def hide_chars(self, is_hidden: bool) -> None:
        if is_hidden:
            self._prev_show_char = self._cget("show")
            self.config(show="")
        else:
            self.config(show=self._prev_show_char)

    @property
    def selection(self) -> str | None:
        if not self._tcl_call(bool, self, "selection", "present"):
            return None
        return self._tcl_call(str, self, "selection", "get")

    @selection.setter
    def selection(
        self, new_selection_range: tuple[int | EndAlias, int | EndAlias] | None  # type: ignore
    ) -> None:
        # it's guite a bad practice that the getter returns a str, but the setter expects a tuple
        if isinstance(new_selection_range, tuple) and len(new_selection_range) == 2:
            start, end = new_selection_range
            self._tcl_call((int,), self, "selection", "range", start, end)
        elif new_selection_range is None:
            self._tcl_call((int,), self, "selection", "clear")
        else:
            warnings.warn(
                "for Entry.selection setter you should use a tuple with two indexes, or"
                + " None to clear the selection",
                stacklevel=3,
            )
