from __future__ import annotations

from typing import Optional, Literal
import warnings

from ._base import BaseWidget, TkWidget

EndAlias = Literal["end"]


class Entry(BaseWidget):
    _keys = {}
    start = 0
    end = "end"

    def __init__(self, parent: Optional[TkWidget] = None) -> None:
        BaseWidget.__init__(self, parent, "ttk::entry")

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __contains__(self, text: str):
        return text in self.get()

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
