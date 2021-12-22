from typing import Callable, Literal, Optional, Union

from ._base import BaseWidget, TkWidget
from ._misc import ScreenDistance
from ._variables import Float


class Slider(BaseWidget):
    _tcl_class = "ttk::scale"
    _keys = {
        "length": ScreenDistance,
        "max": (float, "to"),
        "min": (float, "from"),
        "on_move": ("func", "command"),
        "orientation": (str, "orient"),
        "value": float,
        "variable": Float
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        length: Optional[Union[int, ScreenDistance]] = None,
        max: Optional[int] = 100,
        min: Optional[int] = 0,
        on_move: Optional[Callable] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
        value: Optional[float] = None,
        variable: Optional[Float] = None
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_move,
            from_=min,
            length=length,
            orient=orientation,
            to=max,
            value=value,
            variable=variable
        )

    def _repr_details(self):
        return f"value={self.value!r}"

    def get(self) -> float:
        return self._tcl_call(float, self, "get")

    def set(self, value: float = 0) -> None:
        self._tcl_call(None, self, "set", value)
