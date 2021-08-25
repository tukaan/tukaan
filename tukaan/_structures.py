from .utils import get_tcl_interp

import collections


# TODO: hsl, yiq

class HEX:
    @staticmethod
    def to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def from_hex(hex):
        return tuple(int(hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

class HSV:
    @staticmethod
    def to_hsv(r, g, b):
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

        return tuple(int(x) for x in (h, s, v))

    @staticmethod
    def from_hsv(h, s, v):
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
    def to_cmyk(r, g, b):
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)

        return tuple(int(x * 100) for x in (c, m, y, k))

    @staticmethod
    def from_cmyk(c, m, y, k):
        r = (1 - c / 100) * (1 - k / 100)
        g = (1 - m / 100) * (1 - k / 100)
        b = (1 - y / 100) * (1 - k / 100)

        return tuple(int(x * 255) for x in (r, g, b))


class Color:
    def __init__(self, color, space="hex"):
        if space == "hex":
            rgb = HEX.from_hex(color)
        elif space == "rgb":
            rgb = color
        elif space == "hsv":
            rgb = HSV.from_hsv(*color)
        elif space == "cmyk":
            rgb = CMYK.from_cmyk(*color)
        else:
            raise RuntimeError

        self.red, self.green, self.blue = rgb

    def __repr__(self):
        return f"{type(self).__name__}(red={self.red}, green={self.green}, blue={self.blue})"

    __str__ = __repr__

    def to_tcl(self):
        return self.hex

    @classmethod
    def from_tcl(cls, tcl_value):
        return cls(tcl_value)

    def invert(self):
        self.red = 255 - self.red
        self.green = 255 - self.green
        self.blue = 255 - self.blue

        return self        

    @property
    def hex(self):
        return HEX.to_hex(self.red, self.green, self.blue)

    @property
    def rgb(self):
        return (self.red, self.green, self.blue)

    @property
    def hsv(self):
        return HSV.to_hsv(self.red, self.green, self.blue)

    @property
    def cmyk(self):
        return CMYK.to_cmyk(self.red, self.green, self.blue)

