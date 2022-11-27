from __future__ import annotations

from typing import Any, Callable, Iterable

from tukaan._base import TkWidget, WidgetBase
from tukaan._props import cget, config
from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.widgets.textbox import TextBox


class ComboBox(TextBox):
    _tcl_class = "ttk::combobox"

    def __init__(
        self,
        parent: TkWidget,
        values: dict[str, Any] | None = None,
        *,
        action: Callable | None = None,
        fg_color: str | Color | None = None,
        focusable: bool | None = None,
        hide_chars: bool | None = False,
        hide_chars_with: str | None = "•",
        text_align: str | None = None,
        tooltip: str | None = None,
        user_edit: bool | None = True,
        visible_rows: int | None = None,
        width: int | None = None,
    ) -> None:

        self._prev_show_char = hide_chars_with
        if not hide_chars:
            hide_chars_with = None

        labels = self._setup_values(values)

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
            values=labels,
            width=width,
        )

        self._action = action

        self.bind("<FocusOut>", f"+{self._name} selection clear")
        self.bind("<<ComboboxSelected>>", self._call_action)

        Tcl.call(None, self, "current", 0)

    def __len__(self) -> int:
        return len(Tcl.call([str], self, "cget", "-values"))

    def __iter__(self) -> Iterable[str]:
        return iter(Tcl.call([str], self, "cget", "-values"))

    def __contains__(self, item: str) -> bool:
        return item in Tcl.call([str], self, "cget", "-values")

    def _repr_details(self) -> str:
        selected = self.selected
        if selected:
            plus_str = f"selected='{selected if len(selected) <= 25 else selected[:22] + '...'}'"
        else:
            text = self.text
            plus_str = f"text='{text if len(text) <= 25 else text[:22] + '...'}'"

        selected = self.selected or self.text
        return f"value={self.value!r}, " + plus_str

    def _setup_values(self, values: dict[str, Any] | None) -> list[str] | None:
        if not values:
            self._values = None
            return None

        if isinstance(values, dict):
            self._values = values

            if not all(isinstance(x, str) for x in values.keys()):
                raise TypeError("ComboBox option labels must be strings")

            seen = []
            if any(x in seen or seen.append(x) for x in values.values()):
                raise ValueError("ComboBox option values must be unique")

            return list(values.keys())
        else:
            raise TypeError("must be a dict or None")  # TODO: very informative lol

    def _call_action(self) -> None:
        Tcl.call(None, self, "selection", "clear")
        if self._action is not None:
            self._action(self.value)

    def set(self, value: str) -> None:
        Tcl.call(None, self, "set", value)

    text = property(TextBox.get, set)

    @property
    def value(self) -> Any:
        result = Tcl.call(int, self, "current")
        if result < 0:
            return None

        return list(self._values.values())[result]

    @value.setter
    def value(self, value: Any) -> None:
        if value not in self._values.values():
            raise KeyError

        Tcl.call(None, self, "current", list(self._values.values()).index(value))

    @property
    def selected(self) -> int:
        result = Tcl.call(int, self, "current")
        if result < 0:
            return None

        return list(self._values.keys())[result]

    @selected.setter
    def selected(self, label: str) -> None:
        if label not in self._values:
            raise KeyError

        Tcl.call(None, self, "current", list(self._values.keys()).index(label))

    @property
    def values(self) -> dict[str, Any]:
        return self._values

    @values.setter
    def values(self, values: dict[str, Any] | None) -> None:
        labels = self._setup_values(values)
        if not labels:
            labels = ""
        config(self, values=labels)

    @property
    def popdown_height(self) -> int:
        return cget(self, int, "-height")

    @popdown_height.setter
    def popdown_height(self, value: int) -> None:
        config(self, height=value)

    @property
    def action(self) -> Callable[[str], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[str], None] | None) -> None:
        self._action = func
