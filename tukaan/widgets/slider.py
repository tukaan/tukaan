from __future__ import annotations

from typing import Callable

from tukaan._tcl import Tcl
from tukaan._variables import Float
from tukaan.screen_distance import ScreenDistance

from ._base import BaseWidget, InputControlWidget, TkWidget


class Slider(BaseWidget, InputControlWidget):
    _tcl_class = "ttk::scale"
    _keys = {
        "focusable": (bool, "takefocus"),
        "length": ScreenDistance,
        "max": (float, "to"),
        "min": (float, "from"),
        "on_move": ("func", "command"),
        "orientation": (str, "orient"),
        "value": float,
        "variable": Float,
    }

    def __init__(
        self,
        parent: TkWidget,
        max: int | None = 100,
        *,
        focusable: bool | None = None,
        length: int | ScreenDistance | None = None,
        min: int | None = 0,
        on_move: Callable | None = None,
        orientation: str | None = None,
        value: float | None = None,
        variable: Float | None = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_move,
            from_=min,
            length=length,
            orient=orientation,
            takefocus=focusable,
            to=max,
            value=value,
            variable=variable,
        )

    def _repr_details(self):
        return f"min={self.min!r}, max={self.max!r}, value={self.value!r}"

    def get(self) -> float:
        return Tcl.call(float, self, "get")

    def set(self, value: float = 0) -> None:
        Tcl.call(None, self, "set", value)

    def __add__(self, other: int):
        self.set(self.get() + other)
        return self

    def __sub__(self, other: int):
        self.set(self.get() - other)
        return self
