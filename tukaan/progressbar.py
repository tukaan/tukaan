from typing import Literal, Union

from ._base import BaseWidget, TukaanWidget
from ._utils import get_tcl_interp


class ProgressBar(BaseWidget):
    _keys = {
        "focusable": (bool, "takefocus"),
        "max": int,
        "mode": str,
        "orientation": (str, "orient"),
        "value": int,
    }

    def __init__(
        self,
        parent: Union[TukaanWidget, None] = None,
        focusable: Union[bool, None] = None,
        max: Union[Literal["left", "center", "right"], None] = None,
        mode: Union[Literal["determinate", "indeterminate"], None] = None,
        orientation: Union[Literal["horizontal", "vertical"], None] = None,
        value: int = 50,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            "ttk::progressbar",
            maximum=max,
            mode=mode,
            orient=orientation,
            takefocus=focusable,
            value=value,
        )

    def _repr_details(self):
        return f"mode={self.mode!r}, max={self.max!r}, value={self.value!r}"

    def start(self, steps_per_second: int = 20) -> None:
        if steps_per_second > 1000:
            raise ValueError("error")
        interval = int(1000 / steps_per_second)
        self._tcl_call(None, self, "start", interval)

    def stop(self) -> None:
        self._tcl_call(None, self, "stop")

    def step(self, amount: int = 1) -> None:
        self._tcl_call(None, self, "step", amount)
