from __future__ import annotations

import re
import warnings
from typing import Literal, Optional

from ._base import BaseWidget, TkWidget
from ._misc import Color, ScreenDistance
from ._utils import py_to_tcl_arguments


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
        justify: Optional[Literal["center", "left", "right"]] = None,
        style: Optional[str] = None,
        validation: Optional[Literal["int", "float", "email", "hex-rgb", "hex-rgba"] | str] = None,
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

        self._set_validation(validation)

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __contains__(self, text: str):
        return text in self.get()

    def _set_validation(self, validation):
        self._validation = validation
        vcmd = None
        strict_regex = None
        regex = None

        if validation == "int":
            strict_regex = r"[0-9]"
        elif validation == "float":
            strict_regex = r"[0-9\.]"
            self.bind(
                ("<FocusIn>", "<FocusOut>", "<KeyUp>", "<KeyUp:Enter>"),
                self._validate_float,
            )
        elif validation == "email":
            regex = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
        elif validation == "hex-rgb":
            regex = r"^#(?:[a-fA-F0-9]{3}){1,2}$|#(?:[a-fA-F0-9]{4}){1,2}$"
        elif validation == "hex-rgba":
            regex = r"^#(?:[a-fA-F0-9]{3}){1,2}$"
        elif validation:
            regex = validation

        if regex is not None:
            self.bind(
                ("<FocusIn>", "<FocusOut>", "<KeyUp:Enter>"),
                lambda: self._validate_regex(regex),
            )
        if strict_regex is not None:
            vcmd = (lambda string: self._strict_regex(strict_regex, string), "%S")

        if vcmd is not None:
            self._tcl_call(
                None,
                self,
                "config",
                *py_to_tcl_arguments(validatecommand=vcmd, validate="all"),
            )

    def _repr_details(self) -> str:
        value = self.value
        return f"value='{value if len(value) <= 10 else value[:10] + '...'}'"

    def _strict_regex(self, regex: str, newly_entered: str) -> bool:
        return bool(re.match(regex, newly_entered))

    def _validate_float(self) -> None:
        if self.get() == "":
            return self.state.discard("invalid")
        try:
            float(self.get())
        except ValueError:
            self.state.add("invalid")
        else:
            self.state.discard("invalid")

    def _validate_regex(self, regex: str) -> None:
        if self.get() == "" or re.fullmatch(regex, self.get()):
            self.state.discard("invalid")
        else:
            self.state.add("invalid")

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

    @property
    def validation(self) -> None:
        return self._validation

    @validation.setter
    def validation(self, *_) -> None:
        warnings.warn("Can't update validation. This isn't a modifiable attribute.")

    def x_scroll(self, *args):
        self._tcl_call(None, self, "xview", *args)
