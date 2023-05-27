from __future__ import annotations

from typing import Iterator

from tukaan._base import TkWidget, Widget
from tukaan._properties import EnumDesc, FocusableProp, IntDesc
from tukaan._tcl import Tcl
from tukaan.enums import Orientation, ProgressMode


class ProgressBar(Widget, widget_cmd="ttk::progressbar", tk_class="TProgressbar"):
    focusable = FocusableProp()
    length = IntDesc()
    max = IntDesc()
    mode = EnumDesc(enum=ProgressMode)
    orientation = EnumDesc("orient", Orientation)
    value = IntDesc()

    def __init__(
        self,
        parent: TkWidget,
        max: int = 100,
        *,
        focusable: bool | None = None,
        length: int | None = None,
        mode: ProgressMode | None = None,
        orientation: Orientation | None = None,
        value: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            length=length,
            max=max,
            mode=mode,
            orient=orientation,
            takefocus=focusable,
            value=value,
        )

    def step(self, amount: int = 1) -> None:
        Tcl.call(None, self, "step", amount)

    def start(self, steps_per_second: int = 20) -> None:
        Tcl.call(None, self, "start", 1 / steps_per_second)

    def stop(self) -> None:
        Tcl.call(None, self, "stop")

    def step_through(self) -> Iterator[int]:
        self.value = 0
        yield 0

        for i in range(1, self.max):
            Tcl.call(None, self, "step")
            yield i
