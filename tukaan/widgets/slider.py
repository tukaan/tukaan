from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import cget, config, focusable, link, orientation, value
from tukaan._variables import Float, Integer
from tukaan.enums import Orientation


class Slider(WidgetBase, InputControl):
    _tcl_class = "ttk::scale"

    focusable = focusable
    link = link
    orientation = orientation
    value = value

    def __init__(
        self,
        parent: TkWidget,
        *args,
        focusable: bool | None = None,
        link: Integer | Float | None = None,
        max: float | None = None,
        min: float | None = None,
        on_move: Callable[[float], None] | None = None,
        orientation: Orientation | None = None,
        tooltip: str | None = None,
        value: int | None = None,
    ) -> None:

        if (max is not None and args) or (min is not None and len(args) == 2):
            raise TypeError(
                f"Slider() got multiple values for argument {('max' if max is not None else 'min')!r}"
            )

        if not args and max is None:
            max = 100
        elif len(args) == 1:
            [max] = args
        elif len(args) == 2:
            min, max, *_ = args

        self._original_cmd = on_move
        if on_move is not None:
            func = on_move
            on_move = lambda x: func(float(x))

        self._variable = link

        WidgetBase.__init__(
            self,
            parent,
            command=on_move,
            from_=min,
            orient=orientation,
            takefocus=focusable,
            to=max,
            tooltip=tooltip,
            value=value,
            variable=link,
        )

    def _repr_details(self):
        return f"min={self.min!r}, max={self.max!r}, value={self.value!r}"

    @property
    def bounds(self):
        return cget(self, float, "-from"), cget(self, float, "-to")

    @bounds.setter
    def bounds(self, value: tuple[float, float]):
        from_, to = value
        config(self, from_=from_)
        config(self, to=to)

    @property
    def min(self):
        return cget(self, float, "-from")

    @min.setter
    def min(self, value: float):
        config(self, from_=value)

    @property
    def max(self):
        return cget(self, float, "-to")

    @max.setter
    def max(self, value: float):
        config(self, to=value)

    @property
    def on_move(self) -> Callable[[float], None] | None:
        return self._original_cmd

    @on_move.setter
    def on_move(self, func: Callable[[float], None]) -> None:
        self._original_cmd = func
        value = lambda x: func(float(x))
        config(self, command=value)
