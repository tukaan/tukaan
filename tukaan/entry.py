from __future__ import annotations

import warnings
from typing import Optional

from ._base import BaseWidget, TkWidget
from ._misc import Color, ScreenDistance


class Entry(BaseWidget):
    _tcl_class = "ttk::entry"
    _keys = {
        "color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "hide_chars_with": (str, "show"),
        "justify": str,
        "on_xscroll": ("func", "xscrollcommand"),
        "style": str,
        "width": ScreenDistance,
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
        justify: Optional[str] = None,
        style: Optional[str] = None,
        width: Optional[int] = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        BaseWidget.__init__(
            self,
            parent,
            foreground=color,
            justify=justify,
            show=hide_chars_with,
            style=style,
            takefocus=focusable,
            width=width,
        )

        self.events.bind("<FocusOut>", f"+{self.tcl_path} selection clear")

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __contains__(self, text: str):
        return text in self.get()

    def _repr_details(self) -> str:
        value = self.value
        return f"value='{value if len(value) <= 10 else value[:10] + '...'}'"

    def char_bbox(self, index: int | str):
        result = self._tcl_call((int,), self, "bbox", index)
        return {
            "left": result[0],
            "right": result[0] + result[2],
            "top": result[1],
            "bottom": result[1] + result[3],
        }

    def clear(self) -> None:
        self._tcl_call(None, self, "delete", 0, "end")

    def delete(self, start: int | str, end: int | str = "end") -> None:
        self._tcl_call(None, self, "delete", start, end)

    def get(self) -> str:
        return self._tcl_call(str, self, "get")

    def insert(self, index: int | str, text: str) -> None:
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
            self.config(show=self._prev_show_char)
        else:
            self._prev_show_char = self._cget("show")
            self.config(show="")

    @property
    def selection(self) -> str | None:
        if not self._tcl_call(bool, self, "selection", "present"):
            return None
        return self._tcl_call(str, self, "selection", "get")

    @selection.setter
    def selection(
        self, new_selection_range: tuple[int | str, int | str] | None  # type: ignore
    ) -> None:
        # it's quite a bad thing that the getter returns a str, but the setter expects a tuple
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

    def x_scroll(self, *args):
        self._tcl_call(None, self, "xview", *args)
