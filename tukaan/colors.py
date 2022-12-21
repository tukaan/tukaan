from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from fractions import Fraction

from .exceptions import ColorError

# TODO: refactor this mess


class ColorModel(ABC):
    @staticmethod
    @abstractmethod
    def convert_from():
        pass

    @staticmethod
    @abstractmethod
    def convert_to(*args):
        pass


class Hex(ColorModel):
    @staticmethod
    def convert_from(string):
        int_value = int(string.lstrip("#"), 16)
        return int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF

    @staticmethod
    def convert_to(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"


class Rgb(ColorModel):
    @staticmethod
    def convert_from(r, g, b):
        return r, g, b

    @staticmethod
    def convert_to(r, g, b):
        return r, g, b


class Hsv(ColorModel):
    @staticmethod
    def convert_from(h, s, v):
        h, s, v = h / 360, s / 100, v / 100

        if s == 0.0:
            return tuple(round(x * 255) for x in (v, v, v))

        i = int(h * 6.0)
        f = (h * 6.0) - i

        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))

        r, g, b = (
            (v, t, p),
            (q, v, p),
            (p, v, t),
            (p, q, v),
            (t, p, v),
            (v, p, q),
        )[int(i % 6)]

        return tuple(round(x * 255) for x in (r, g, b))

    @staticmethod
    def convert_to(r, g, b):
        r, g, b = tuple(x / 255 for x in (r, g, b))

        high = max(r, g, b)
        low = min(r, g, b)
        diff = high - low

        h = 0
        s = 0 if high == 0 else (diff / high) * 100
        v = high * 100

        if high == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif high == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        elif high == b:
            h = (60 * ((r - g) / diff) + 240) % 360

        return tuple(round(x) for x in (h, s, v))


class Hsl(ColorModel):
    @staticmethod
    def convert_from(h, s, l):
        h, s, l = h / 360, s / 100, l / 100

        if s == 0.0:
            return (round(l * 255),) * 3

        if l >= 0.5:
            tmp_1 = l + s - l * s
        elif l < 0.5:
            tmp_1 = l * (1 + s)

        tmp_2 = 2 * l - tmp_1

        def _(h):
            h = h % 1
            if h < 1 / 6:
                return tmp_2 + (tmp_1 - tmp_2) * h * 6
            if h < 0.5:
                return tmp_1
            if h < 2 / 3:
                return tmp_2 + (tmp_1 - tmp_2) * (2 / 3 - h) * 6
            return tmp_2

        r = _(h + 1 / 3)
        g = _(h)
        b = _(h - 1 / 3)

        return tuple(round(x) for x in (r * 255, g * 255, b * 255))

    @staticmethod
    def convert_to(r, g, b):
        r, g, b = r / 255, g / 255, b / 255
        min_value = min(r, g, b)
        max_value = max(r, g, b)

        l = (min_value + max_value) / 2

        if min_value == max_value:
            return (0, 0, round(l * 100))

        if l <= 0.5:
            s = (max_value - min_value) / (max_value + min_value)
        elif l > 0.5:
            s = (max_value - min_value) / (2.0 - max_value - min_value)

        if max_value == r:
            h = (g - b) / (max_value - min_value)
        elif max_value == g:
            h = 2.0 + (b - g) / (max_value - min_value)
        elif max_value == b:
            h = 4.0 + (r - g) / (max_value - min_value)

        return tuple(round(x) for x in (h * 60, s * 100, l * 100))


class Cmyk(ColorModel):
    @staticmethod
    def convert_from(c, m, y, k) -> tuple[int, ...]:
        c = c / 100.0
        m = m / 100.0
        y = y / 100.0
        k = k / 100.0

        r = 255.0 - ((min(1.0, c * (1.0 - k) + k)) * 255.0)
        g = 255.0 - ((min(1.0, m * (1.0 - k) + k)) * 255.0)
        b = 255.0 - ((min(1.0, y * (1.0 - k) + k)) * 255.0)

        return tuple(round(x) for x in (r, g, b))

    @staticmethod
    def convert_to(r, g, b) -> tuple[int, ...]:
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 100)

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = c - k
        m = m - k
        y = y - k

        return tuple(round(x * 100) for x in (c, m, y, k))


def cmyk(c, m, y, k):
    return Hex.convert_to(*Cmyk.convert_from(c, m, y, k))


def hsl(h, s, l):
    return Hex.convert_to(*Hsl.convert_from(h, s, l))


def hsv(h, s, v):
    return Hex.convert_to(*Hsv.convert_from(h, s, v))


def rgb(r, g, b):
    return Hex.convert_to(r, g, b)


@dataclass
class Color:
    red: int
    green: int
    blue: int

    def __init__(self, color: str = None, **kwargs):
        if len(kwargs) != 1:
            if color:
                value = color
                factory = Hex
            else:
                raise ColorError("multiple colors specified")
        else:
            model = tuple(kwargs.keys())[0]
            value = kwargs[model]
            try:
                factory = {
                    "cmyk": Cmyk,
                    "hex": Hex,
                    "hsl": Hsl,
                    "hsv": Hsv,
                    "rgb": Rgb,
                }[model]
            except KeyError:
                raise ColorError(f"invalid color model name: {model}") from None

        if factory is Hex:
            value = (value,)

        self.red, self.green, self.blue = factory.convert_from(*value)

    def __to_tcl__(self) -> str:
        return Hex.convert_to(self.red, self.green, self.blue)

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> Color:
        return Color(rgb=Hex.convert_from(tcl_value))

    @property
    def is_dark(self) -> bool:
        return ((self.red * 299 + self.green * 587 + self.blue * 114) / 1000) < 128

    def invert(self) -> Color:
        return Color(rgb=(255 - self.red, 255 - self.green, 255 - self.blue))

    __invert__ = invert

    def mix(self, other: Color, ratio: float) -> Color:
        if not isinstance(other, Color):
            raise TypeError

        a, b = Fraction.from_float(ratio).as_integer_ratio()
        amount_of_clr_1 = 1 / (a + b) * a
        amount_of_clr_2 = 1 / (a + b) * b

        r, g, b = (
            round(amount_of_clr_1 * value1 + amount_of_clr_2 * value2)
            for value1, value2 in zip(self.rgb, other.rgb)
        )
        return Color(rgb=(r, g, b))

    def __or__(self, other: Color) -> Color:
        return self.mix(other, 1 / 1)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def hex(self) -> str:
        return Hex.convert_to(self.red, self.green, self.blue)

    @property
    def hsl(self) -> tuple[int, int, int]:
        return Hsl.convert_to(self.red, self.green, self.blue)

    @property
    def hsv(self) -> tuple[int, int, int]:
        return Hsv.convert_to(self.red, self.green, self.blue)

    @property
    def cmyk(self) -> tuple[int, int, int, int]:
        return Cmyk.convert_to(self.red, self.green, self.blue)
