from typing import Literal, Optional

from ._base import BaseWidget, TkWidget


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
        parent: Optional[TkWidget] = None,
        focusable: Optional[bool] = None,
        max: Optional[Literal["left", "center", "right"]] = None,
        mode: Optional[Literal["determinate", "indeterminate"]] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
        value: Optional[int] = None,
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

    def get(self) -> float:
        return self.value

    def set(self, value: float = 0) -> None:
        self.value = value

    def start(self, steps_per_second: int = 20) -> None:
        if steps_per_second > 1000:
            raise ValueError("error")
        interval = int(1000 / steps_per_second)
        self._tcl_call(None, self, "start", interval)

    def stop(self) -> None:
        self._tcl_call(None, self, "stop")

    def step(self, amount: int = 1) -> None:
        self._tcl_call(None, self, "step", amount)
