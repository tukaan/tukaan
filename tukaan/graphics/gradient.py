from __future__ import annotations

from math import cos, radians, sin, tan
from typing import TYPE_CHECKING

from tukaan._tcl import Tcl
from tukaan._utils import seq_pairs

if TYPE_CHECKING:
    from .canvas import Canvas


class Gradient:
    def __init__(self, parent: Canvas) -> None:
        self._canvas = parent

    def __from_tcl__(self, gradient_name: str) -> Gradient:
        gradient = {"linear": LinearGradient, "radial": RadialGradient}[
            Tcl.call(str, self._canvas, "gradient", "type", gradient_name)
        ](self._canvas)
        gradient._name = gradient_name
        return gradient

    @property
    def in_use(self) -> bool:
        return Tcl.call(bool, self._canvas, "gradient", "inuse", self)

    @property
    def stops(self):
        result = Tcl.call((str,), self._canvas, "gradient", "cget", self, "-stops")

        result_dict = {}
        for x in result:
            k, v = x.split(" ")
            result_dict[float(k)] = v

        return result_dict

    @stops.setter
    def stops(self, new_stops) -> None:
        Tcl.call(
            None,
            self._canvas,
            "gradient",
            "configure",
            self,
            "-stops",
            self._process_stops(new_stops),
        )

    def dispose(self) -> None:
        Tcl.call(None, self._canvas, "gradient", "delete", self)

    def _process_stops(self, stops: list[str] | tuple[str, ...] | dict[int, str]):
        if not isinstance(stops, dict):
            step = 1 / (len(stops) - 1)
            stops = {(step * index): color for index, color in enumerate(stops)}

        result = list(seq_pairs(Tcl.to(stops)))
        result.sort(key=lambda e: e[0])
        return result


class LinearGradient(Gradient):
    def __call__(
        self, stops: list[str] | tuple[str, ...] | dict[int, str], *, angle: int = 0
    ) -> Gradient:
        angle_sin = sin(radians(angle))
        angle_cos = cos(radians(angle))

        if 0 <= angle <= 90:
            ltransition = (0, 0, angle_cos, angle_sin)
        elif 90 < angle <= 180:
            ltransition = (-angle_cos, 0, 0, angle_sin)
        elif 180 < angle <= 270:
            ltransition = (-angle_cos, -angle_sin, 0, 0)
        elif 270 < angle <= 360:
            ltransition = (0, -angle_sin, angle_cos, 0)
        else:
            raise ValueError("angle must be between 0 and 360")

        self._name = Tcl.call(
            str,
            self._canvas,
            "gradient",
            "create",
            "linear",
            "-stops",
            self._process_stops(stops),
            *Tcl.to_tcl_args(lineartransition=ltransition),
        )
        return self


class RadialGradient(Gradient):
    def __call__(
        self,
        stops: list[str] | tuple[str, ...] | dict[int, str],
        *,
        center: int | tuple[int, int] = 0.5,
        last_center: int | tuple[int, int] = 0.5,
        radius: int = 0.5,
    ) -> Gradient:
        if isinstance(center, (tuple, list)):
            fx, fy = center
        else:
            fx = fy = center

        if isinstance(last_center, (tuple, list)):
            cx, cy = last_center
        else:
            cx = cy = last_center

        self._name = Tcl.call(
            str,
            self._canvas,
            "gradient",
            "create",
            "radial",
            "-stops",
            self._process_stops(stops),
            *Tcl.to_tcl_args(radialtransition=(cx, cy, radius, fx, fy)),
        )
        return self
