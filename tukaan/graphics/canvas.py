from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from tukaan._base import TkWidget, WidgetBase
from tukaan._tcl import Tcl
from .equipment import Brush, Pen
from .gradient import LinearGradient, RadialGradient, Gradient
from tukaan.colors import Color


class Canvas(WidgetBase):
    _tcl_class = "::tkp::canvas"

    def __init__(
        self,
        parent: TkWidget,
        *,
        width: int | None = 400,
        height: int | None = 400,
        bg_color: Color | str | None = None,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            background=bg_color,
            borderwidth=0,
            highlightthickness=0,
        )

        self.brush = Brush()
        self.pen = Pen()

        self._gradient_superclass = Gradient(self)
        self.linear_gradient = LinearGradient(self)
        self.radial_gradient = RadialGradient(self)
