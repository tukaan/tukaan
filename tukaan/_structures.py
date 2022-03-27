from __future__ import annotations

from abc import ABC, abstractstaticmethod
from collections import namedtuple

Bbox = namedtuple("Bbox", ["x", "y", "width", "height"])
Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])


class Color:
    ...


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
        int_value = int(hex.lstrip("#"), 16)
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
