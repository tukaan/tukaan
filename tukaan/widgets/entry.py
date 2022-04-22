from __future__ import annotations

from typing import Iterable

from tukaan._structures import Bbox
from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.exceptions import TclError

from ._base import BaseWidget, InputControlWidget, TkWidget, XScrollable


class Entry(BaseWidget, InputControlWidget, XScrollable):
    _tcl_class = "ttk::entry"
    _keys = {
        "fg_color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "hide_chars_with": (str, "show"),
        "justify": str,
        "on_xscroll": ("func", "xscrollcommand"),
        "style": str,
        "width": int,
    }

    start = 0
    end = "end"

    def __init__(
        self,
        parent: TkWidget,
        *,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool = False,
        hide_chars_with: str | None = "•",
        justify: str | None = None,
        style: str | None = None,
        user_edit: bool | None = True,
        value: str | None = None,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        BaseWidget.__init__(
            self,
            parent,
            foreground=fg_color,
            justify=justify,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            style=style,
            takefocus=focusable,
            width=width,
        )

        self.bind("<FocusOut>", f"+{self._name} selection clear")

        if value:
            self.set(value)

    def __len__(self):
        return len(self.get())

    def __iter__(self) -> Iterable[str]:
        return iter(self.get())

    def __contains__(self, text: str) -> bool:
        return text in self.get()

    def _repr_details(self) -> str:
        value = self.value
        return f"value='{value if len(value) <= 10 else value[:10] + '...'}'"

    def char_bbox(self, index: int | str):
        return Bbox(*Tcl.call((int,), self, "bbox", index))

    def clear(self) -> None:
        Tcl.call(None, self, "delete", 0, "end")

    def delete(self, start: int | str, end: int | str = "end") -> None:
        Tcl.call(None, self, "delete", start, end)

    def get(self, *indices) -> str:
        content = Tcl.call(str, self, "get")

        if indices and indices[0] != None:
            if not isinstance(indices[0], (str, float)):
                indices = indices[0]
            return content[indices[0] : indices[1]]

        return content

    def set(self, new_value: str) -> None:
        Tcl.call(None, self, "delete", 0, "end")
        Tcl.call(None, self, "insert", 0, new_value)

    value = property(get, set)

    def insert(self, index: int | str, text: str) -> None:
        Tcl.call(None, self, "insert", index, text)

    @property
    def caret_pos(self) -> int:
        return Tcl.call(int, self, "index", "insert")

    @caret_pos.setter
    def caret_pos(self, new_pos: int) -> None:
        Tcl.call(None, self, "icursor", new_pos)

    @property
    def hide_chars(self) -> bool:
        return self.hide_chars_with != ""

    @hide_chars.setter
    def hide_chars(self, is_hidden: bool) -> None:
        if is_hidden:
            self.config(show=self._prev_show_char)
        else:
            self._prev_show_char = self._cget("show")
            self.config(show="")

    @property
    def selection(self) -> str | None:
        try:
            first = Tcl.call(int, self, "index", "sel.first")
            last = Tcl.call(int, self, "index", "sel.last")
        except TclError:
            return None
        else:
            return first, last

    @selection.setter
    def selection(self, new_range: tuple[int | str, int | str] | list[int | str] | None) -> None:
        if isinstance(new_range, (tuple, list)) and len(new_range) == 2:
            start, end = new_range
            Tcl.call((int,), self, "selection", "range", start, end)
        elif new_range is None:
            Tcl.call((int,), self, "selection", "clear")
