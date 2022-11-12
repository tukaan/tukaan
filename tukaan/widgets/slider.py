from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import FloatDesc, FocusableProp, LinkProp, OrientProp, cget, config
from tukaan._variables import FloatVar, IntVar
from tukaan.enums import Orientation


class Slider(WidgetBase, InputControl):
    _tcl_class = "ttk::scale"

    focusable = FocusableProp()
    target = LinkProp()
    orientation = OrientProp()
    value = FloatDesc("value")

    def __init__(
        self,
        parent: TkWidget,
        min: float | None = None,
        max: float | None = None,
        *,
        action: Callable[[float], None] | None = None,
        focusable: bool | None = None,
        orientation: Orientation | None = None,
        target: IntVar | FloatVar | None = None,
        tooltip: str | None = None,
        value: float | None = None,
    ) -> None:
        self._variable = target
        self._action = action
        self._prev_value = value or 0

        WidgetBase.__init__(
            self,
            parent,
            command=self._call_action,
            from_=min,
            orient=orientation,
            takefocus=focusable,
            to=100 if max is None else max,
            tooltip=tooltip,
            value=min if value is None else value,
            variable=target,
        )

    def _repr_details(self) -> str:
        return f"min={self.min!r}, max={self.max!r}, value={self.value!r}"

    def _call_action(self, value: str) -> None:
        if self._action is not None and self._prev_value != value:
            self._action(float(value))
        self._prev_value = value

    @property
    def bounds(self) -> tuple[float, float]:
        return cget(self, float, "-from"), cget(self, float, "-to")

    @bounds.setter
    def bounds(self, value: tuple[float, float]) -> None:
        from_, to = value
        config(self, from_=from_)
        config(self, to=to)

    @property
    def min(self) -> float:
        return cget(self, float, "-from")

    @min.setter
    def min(self, value: float) -> None:
        config(self, from_=value)

    @property
    def max(self) -> float:
        return cget(self, float, "-to")

    @max.setter
    def max(self, value: float) -> None:
        config(self, to=value)

    @property
    def action(self) -> Callable[[str], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[str], None] | None) -> None:
        self._action = func
