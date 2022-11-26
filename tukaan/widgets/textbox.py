from __future__ import annotations

from typing import Iterable

from tukaan._base import InputControl, TkWidget, WidgetBase, XScrollable
from tukaan._misc import Bbox
from tukaan._props import FocusableProp, ForegroundProp, TextAlignProp, WidthProp, cget, config
from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.exceptions import TukaanTclError


class TextBox(WidgetBase, InputControl, XScrollable):
    _tcl_class = "ttk::entry"

    fg_color = ForegroundProp()
    focusable = FocusableProp()
    text_align = TextAlignProp()
    width = WidthProp()

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
        text_align: str | None = None,
        tooltip: str | None = None,
        user_edit: bool | None = True,
        value: str | None = None,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        WidgetBase.__init__(
            self,
            parent,
            foreground=fg_color,
            justify=text_align,
            show=hide_chars_with,
            state=None if user_edit else "readonly",
            takefocus=focusable,
            tooltip=tooltip,
            width=width,
        )

        self.bind("<FocusOut>", f"+{self._name} selection clear")

        if value:
            self.set(value)

    def __len__(self) -> int:
        return len(self.get())

    def __iter__(self) -> Iterable[str]:
        return iter(self.get())

    def __contains__(self, text: str) -> bool:
        return text in self.get()

    def _repr_details(self) -> str:
        value = self.value
        return f"value='{value if len(value) <= 10 else value[:10] + '...'}'"

    def insert(self, index: int | str | None, string: str) -> None:
        if index is None:
            index = "insert"
        elif isinstance(index, int) and index < 0:
            index = f"end - {index} chars"

        Tcl.call(None, self, "insert", index, string)

    def delete(self, start: int | str, end: int | str = "end") -> None:
        Tcl.call(None, self, "delete", start, end)

    def clear(self) -> None:
        Tcl.call(None, self, "delete", 0, "end")

    def __getitem__(self, indices: slice) -> str:
        return Tcl.call(str, self, "get")[indices]

    def get(self, *indices) -> str:
        if indices:
            return self[slice(*indices)]
        return Tcl.call(str, self, "get")

    def set(self, value: str) -> None:
        Tcl.call(None, self, "delete", 0, "end")
        Tcl.call(None, self, "insert", 0, value)

    text = property(get, set)

    def char_bbox(self, index: int | str) -> Bbox:
        return Bbox(*Tcl.call((int,), self, "bbox", index))

    @property
    def hide_chars_with(self) -> str:
        return cget(self, str, "-show")

    @hide_chars_with.setter
    def hide_chars_with(self, value: str) -> None:
        config(self, show=value)

    @property
    def hide_chars(self) -> bool:
        return cget(self, str, "-show") != ""

    @hide_chars.setter
    def hide_chars(self, value: bool) -> None:
        if value:
            config(self, show=self._prev_show_char)
        else:
            self._prev_show_char = cget(self, str, "-show")
            config(self, show="")

    @property
    def user_edit(self) -> bool:
        return cget(self, str, "-state") != "readonly"

    @user_edit.setter
    def user_edit(self, value: bool) -> None:
        config(self, state="normal" if value else "readonly")

    @property
    def caret_pos(self) -> int:
        return Tcl.call(int, self, "index", "insert")

    @caret_pos.setter
    def caret_pos(self, value: int) -> None:
        Tcl.call(None, self, "icursor", value)

    @property
    def selection(self) -> tuple[int, int] | None:
        try:
            first = Tcl.call(int, self, "index", "sel.first")
            last = Tcl.call(int, self, "index", "sel.last")
        except TukaanTclError:
            return None
        else:
            return first, last

    @selection.setter
    def selection(self, value: tuple[int | str, int | str] | None) -> None:
        if value is None:
            Tcl.call(None, self, "selection", "clear")
        elif isinstance(value, (tuple, list)):
            Tcl.call(None, self, "selection", "range", *value)
