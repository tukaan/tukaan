from __future__ import annotations

from typing import Tuple, Union

from .utils import get_tcl_interp


class HEX:
    @staticmethod
    def to_hex(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def from_hex(hex) -> tuple:
        int_value = int(hex[1:], 16)
        return (int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF)


class HSV:
    @staticmethod
    def to_hsv(r, g, b) -> tuple:
        r, g, b = tuple(x / 255 for x in (r, g, b))

        high = max(r, g, b)
        low = min(r, g, b)
        diff = high - low

        if high == low:
            h = 0
        elif high == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif high == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        elif high == b:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if high == 0 else (diff / high) * 100
        v = high * 100

        return tuple(x for x in (h, s, v))

    @staticmethod
    def from_hsv(h, s, v) -> tuple:
        h, s, v = h / 360, s / 100, v / 100

        if s == 0.0:
            return tuple(int(x * 255) for x in (v, v, v))

        i = int(h * 6.0)
        f = (h * 6.0) - i

        p, q, t = (
            v * (1.0 - s),
            v * (1.0 - s * f),
            v * (1.0 - s * (1.0 - f)),
        )

        r, g, b = [
            (v, t, p),
            (q, v, p),
            (p, v, t),
            (p, q, v),
            (t, p, v),
            (v, p, q),
        ][int(i % 6)]

        return tuple(int(x * 255) for x in (r, g, b))


class CMYK:
    @staticmethod
    def to_cmyk(r, g, b) -> tuple:
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)

        return tuple(int(x * 100) for x in (c, m, y, k))

    @staticmethod
    def from_cmyk(c, m, y, k) -> tuple:
        r = (1 - c / 100) * (1 - k / 100)
        g = (1 - m / 100) * (1 - k / 100)
        b = (1 - y / 100) * (1 - k / 100)

        return tuple(int(x * 255) for x in (r, g, b))


# TODO: hsl, yiq
class Color:
    def __init__(self, color, space: str = "hex") -> None:
        if space == "hex":
            rgb = HEX.from_hex(color)
        elif space == "rgb":
            rgb = color
        elif space == "hsv":
            rgb = HSV.from_hsv(*color)
        elif space == "cmyk":
            rgb = CMYK.from_cmyk(*color)
        else:
            raise ValueError

        self.red, self.green, self.blue = rgb

    def __repr__(self) -> str:
        return f"{type(self).__name__}(red={self.red}, green={self.green}, blue={self.blue})"

    __str__ = __repr__

    def to_tcl(self) -> str:
        return self.hex

    @classmethod
    def from_tcl(cls, tcl_value) -> Color:
        return cls(tcl_value)

    def invert(self) -> Color:
        self.red = 255 - self.red
        self.green = 255 - self.green
        self.blue = 255 - self.blue

        return self

    @property
    def hex(self) -> str:
        return HEX.to_hex(self.red, self.green, self.blue)

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def hsv(self) -> tuple:
        return HSV.to_hsv(self.red, self.green, self.blue)

    @property
    def cmyk(self) -> tuple:
        return CMYK.to_cmyk(self.red, self.green, self.blue)


class ScreenDistance:
    _tcl_units = {"px": "", "mm": "m", "cm": "c", "m": "c", "inch": "i", "ft": "i"}

    def __init__(self, distance, unit="px") -> None:
        if unit != "px":
            distance = f"{distance}{self._tcl_units[unit]}"

            pixels = get_tcl_interp().tcl_call(float, "winfo", "fpixels", ".", distance)

            if unit == "m":
                pixels *= 100
            elif unit == "ft":
                pixels *= 12

        else:
            pixels = distance

        self.dpi = get_tcl_interp().tcl_call(float, "winfo", "fpixels", ".", "1i")
        self.distance = pixels

    def __repr__(self) -> str:
        return f"{type(self).__name__}(distance={round(self.distance, 4)} pixels)"

    __str__ = __repr__

    def to_tcl(self) -> str:
        return self.distance

    @classmethod
    def from_tcl(cls, tcl_value: int) -> ScreenDistance:
        return cls(tcl_value)

    @property
    def px(self) -> float:
        return round(self.distance, 4)

    @property
    def mm(self) -> float:
        return round(self.distance / (self.dpi / 25.4), 4)

    @property
    def cm(self) -> float:
        return round(self.distance / (self.dpi / 2.54), 4)

    @property
    def m(self) -> float:
        return round(self.distance / (self.dpi / 0.0254), 4)

    @property
    def inch(self) -> float:
        return round(self.distance / self.dpi, 4)

    @property
    def ft(self) -> float:
        return round(self.distance / (self.dpi * 12), 4)
