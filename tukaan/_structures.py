from __future__ import annotations

from abc import ABC, abstractstaticmethod
from collections import namedtuple
from dataclasses import dataclass
from fractions import Fraction

Bbox = namedtuple("Bbox", ["x", "y", "width", "height"])
Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])
OsVersion = namedtuple("OsVersion", ["major", "minor", "build"])
Version = namedtuple("Version", ["major", "minor", "patchlevel"])


@dataclass
class Color:
    red: int
    green: int
    blue: int

    def __to_tcl__(self) -> str:
        return self.hex

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> Color:
        return cls(*hex._from(tcl_value))

    def invert(self) -> Color:
        self.red = 255 - self.red
        self.green = 255 - self.green
        self.blue = 255 - self.blue

        return self

    def mix(self, other, ratio):
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

    def __or__(self, other):
        return self.mix(other, 1 / 1)

    @property
    def is_dark(self):
        return ((self.red * 299 + self.green * 587 + self.blue * 114) / 1000) < 128

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def hex(self) -> str:
        return hex._to(self.red, self.green, self.blue)

    @property
    def hsl(self) -> tuple[int, int, int]:
        return hsl._to(self.red, self.green, self.blue)

    @property
    def hsv(self) -> tuple[int, int, int]:
        return hsv._to(self.red, self.green, self.blue)

    @property
    def cmyk(self) -> tuple[int, int, int, int]:
        return cmyk._to(self.red, self.green, self.blue)


class ColorFactory(ABC):
    def __new__(cls, r, g, b):
        return hex._to(r, g, b)

    @abstractstaticmethod
    def _to(r, g, b):
        ...

    @abstractstaticmethod
    def _from(color) -> tuple[int, int, int]:
        ...


class rgb(ColorFactory):
    def _to(r, g, b) -> str:
        return r, g, b

    def _from(r, g, b) -> tuple[int, ...]:
        return r, g, b


class hex(ColorFactory):
    def __new__(cls, string):
        return string

    def _to(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    def _from(string) -> tuple[int, ...]:
        int_value = int(string.lstrip("#"), 16)
        return int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF


class hsl(ColorFactory):
    def __new__(cls, h, s, l):
        return hex._to(*cls._from(h, s, l))

    def _to(r, g, b) -> tuple[int, ...]:
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

    def _from(h, s, l) -> tuple[int, ...]:
        h, s, l = h / 360, s / 100, l / 100

        if s == 0.0:
            return (round(l * 255),) * 3

        if l >= 0.5:
            tmp_1 = l + s - l * s
        elif l < 0.5:
            tmp_1 = l * (1 + s)

        tmp_2 = 2 * l - tmp_1

        def func(h):
            h = h % 1
            if h < 1 / 6:
                return tmp_2 + (tmp_1 - tmp_2) * h * 6
            if h < 0.5:
                return tmp_1
            if h < 2 / 3:
                return tmp_2 + (tmp_1 - tmp_2) * (2 / 3 - h) * 6
            return tmp_2

        r = func(h + 1 / 3)
        g = func(h)
        b = func(h - 1 / 3)

        return tuple(round(x) for x in (r * 255, g * 255, b * 255))


class hsv:
    def __new__(cls, h, s, v):
        return hex._to(*cls._from(h, s, v))

    def _to(r, g, b) -> tuple[int, ...]:
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

    def _from(h, s, v) -> tuple[int, ...]:
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


class cmyk(ColorFactory):
    def __new__(cls, c, m, y, k):
        return hex._to(*cls._from(c, m, y, k))

    def _to(r, g, b) -> tuple[int, ...]:
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 100)

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = c - k
        m = m - k
        y = y - k

        return tuple(round(x * 100) for x in (c, m, y, k))

    def _from(c, m, y, k) -> tuple[int, ...]:
        c = c / 100.0
        m = m / 100.0
        y = y / 100.0
        k = k / 100.0

        r = 255.0 - ((min(1.0, c * (1.0 - k) + k)) * 255.0)
        g = 255.0 - ((min(1.0, m * (1.0 - k) + k)) * 255.0)
        b = 255.0 - ((min(1.0, y * (1.0 - k) + k)) * 255.0)

        return tuple(round(x) for x in (r, g, b))


class Time:
    def __init__(self, *args, **kwargs):
        if args and not kwargs:
            if len(args) == 3:
                h, m, s = args
                if s is None and m is None:  # comes from a slice
                    h, m, s = 0, 0, h
                elif s is None:
                    h, m, s = 0, h, m
            elif len(args) == 2:
                h, m, s = 0, *args
            elif len(args) == 1:
                h, m, s = 0, 0, args[0]
        elif kwargs and not args:
            h = kwargs.pop("hours", 0)
            m = kwargs.pop("minutes", 0)
            s = kwargs.pop("seconds", 0)
        else:
            raise ValueError

        if s >= 60:
            plus_m, s = divmod(s, 60)
            m += plus_m
        if m >= 60:
            plus_h, m = divmod(m, 60)
            h += plus_h

        self.hours = int(h)
        self.minutes = int(m)
        self.seconds = s

    def __repr__(self):
        time_values = [self.hours, self.minutes, self.seconds]
        if not time_values[0]:
            del time_values[0]
            
        return f"Time[{':'.join(map(str, time_values))}]"

    @property
    def total_seconds(self):
        return self.hours * 3600 + self.minutes * 60 + self.seconds


class _TimeConstructor:
    def __getitem__(self, key):
        if isinstance(key, slice):
            return Time(key.start, key.stop, key.step)
        elif isinstance(key, (int, float)):
            return Time(seconds=key)

    def __call__(self, *args, **kwargs):
        return Time(*args, **kwargs)

    def __instancecheck__(self, other):
        return isinstance(other, (_TimeConstructor, Time))

    def __repr__(self):
        return "<tukaan.Time; usage: Time[h:min:sec] or Time(h, min, sec)>"

    @staticmethod
    def from_secs(seconds: int):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return Time(h, m, s)


_Time = _TimeConstructor()
