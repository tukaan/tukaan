from typing import Callable, Literal, Optional, Union

from ._base import BaseWidget, TukaanWidget
from ._misc import ScreenDistance
from ._returntype import Callback


class Slider(BaseWidget):
    _keys = {
        "length": ScreenDistance,
        "max": (int, "to"),
        "min": (int, "from"),
        "on_move": (Callback, "command"),
        "orientation": (str, "orient"),
        "value": float,
    }

    def __init__(
        self,
        parent: Optional[TukaanWidget] = None,
        length: Optional[Union[int, ScreenDistance]] = None,
        max: Optional[int] = None,
        min: Optional[int] = None,
        on_move: Optional[Callable] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
        value: Optional[float] = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            "ttk::scale",
            command=on_move,
            from_=min,
            length=length,
            orient=orientation,
            to=max,
            value=value,
        )

    def _repr_details(self):
        return f"value={self.value!r}"

    def get(self) -> float:
        return self._tcl_call(float, self, "get")

    def set(self, value: float = 0) -> None:
        self._tcl_call(None, self, "set", value)
