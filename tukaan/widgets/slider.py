from typing import Callable, Literal, Optional, Union

from ._base import BaseWidget, TkWidget
from tukaan._units import ScreenDistance
from tukaan._variables import Float
from tukaan._tcl import Tcl


class Slider(BaseWidget):
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
        parent: Optional[TkWidget] = None,
        max: Optional[int] = 100,
        *,
        focusable: Optional[bool] = None,
        length: Optional[Union[int, ScreenDistance]] = None,
        min: Optional[int] = 0,
        on_move: Optional[Callable] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
        value: Optional[float] = None,
        variable: Optional[Float] = None,
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
