from __future__ import annotations

from typing import Generator

from tukaan._base import OutputDisplay, TkWidget, WidgetBase
from tukaan._props import FocusableProp, IntDesc, LinkProp, OrientProp, cget, config
from tukaan._tcl import Tcl
from tukaan._variables import FloatVar, IntVar
from tukaan.enums import Orientation, ProgressMode
from tukaan.timeouts import Timeout


class ProgressBar(WidgetBase, OutputDisplay):
    _tcl_class = "ttk::progressbar"

    focusable = FocusableProp()
    orientation = OrientProp()
    value = IntDesc("value")
    link = LinkProp()

    _timeout = None

    def __init__(
        self,
        parent: TkWidget,
        length: int = 100,
        *,
        focusable: bool | None = None,
        link: IntVar | FloatVar | None = None,
        mode: ProgressMode | None = None,
        orientation: Orientation | None = None,
        tooltip: str | None = None,
        value: int | None = None,
    ) -> None:
        self._max = length

        WidgetBase.__init__(
            self,
            parent,
            max=length,
            mode=mode,
            orient=orientation,
            takefocus=focusable,
            tooltip=tooltip,
            value=value,
            variable=link,
        )

    def _repr_details(self) -> str:
        return f"mode={self.mode!r}, length={self._max!r}, value={self.value!r}"

    def step(self, amount: int = 1) -> None:
        Tcl.call(None, self, "step", amount)

    def start_progress(self, steps_per_second: int = 20) -> None:
        self._timeout = Timeout(1 / steps_per_second, self.step)
        self._timeout.repeat()

    def stop_progress(self) -> None:
        if self._timeout is not None:
            self._timeout.cancel()

    def through(self) -> Generator[int, None, None]:
        self.value = 0
        yield 0

        for i in range(1, self._max):
            Tcl.call(None, self._name, "step")
            yield i

    # Properties #

    @property
    def length(self) -> int:
        return cget(self, int, "-max")

    @length.setter
    def length(self, value: int) -> None:
        self._max = value
        return config(self, max=value)

    @property
    def mode(self) -> ProgressMode:
        return cget(self, ProgressMode, "-mode")

    @mode.setter
    def mode(self, value: ProgressMode) -> None:
        return config(self, mode=value)
