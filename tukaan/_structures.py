from __future__ import annotations

import collections
from typing import List, Tuple, Union, cast

# fmt: off
from .utils import (ClassPropertyMetaClass, classproperty, get_tcl_interp,
                    update_before)


class HEX:
    @staticmethod
    def to_hex(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def from_hex(hex) -> Tuple[int, int, int]:
        int_value = int(hex[1:], 16)
        return cast(
            Tuple[int, int, int],
            (int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF),
        )


class HSV:
    @staticmethod
    def to_hsv(r, g, b) -> Tuple[int, int, int]:
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

        return cast(Tuple[int, int, int], tuple(int(x) for x in (h, s, v)))

    @staticmethod
    def from_hsv(h, s, v) -> Tuple[int, int, int]:
        h, s, v = h / 360, s / 100, v / 100

        if s == 0.0:
            return cast(Tuple[int, int, int], tuple(int(x * 255) for x in (v, v, v)))

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

        return cast(Tuple[int, int, int], tuple(int(x * 255) for x in (r, g, b)))


class CMYK:
    @staticmethod
    def to_cmyk(r, g, b) -> Tuple[int, int, int, int]:
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)

        return cast(
            Tuple[int, int, int, int], tuple(int(x * 100) for x in (c, m, y, k))
        )

    @staticmethod
    def from_cmyk(c, m, y, k) -> Tuple[int, int, int]:
        r = (1 - c / 100) * (1 - k / 100)
        g = (1 - m / 100) * (1 - k / 100)
        b = (1 - y / 100) * (1 - k / 100)

        return cast(Tuple[int, int, int], tuple(int(x * 255) for x in (r, g, b)))


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
    """An object to convert between different screen distance units"""

    # TODO: make this an immutable object?
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


class Cursor(
    collections.namedtuple("Cursor", "cursor"), metaclass=ClassPropertyMetaClass
):
    """An object to use cross-platform, and human-understandable cursor names,
    and to get and set the mouse cursor position"""

    cursor_dict = {
        "center": "center_ptr",
        "crosshair": "crosshair",
        "default": "arrow",
        "e-resize": "right_side",
        "ew-resize": "sb_h_double_arrow",
        "help": "question_arrow",
        "move": "fleur",
        "n-resize": "top_side",
        "ne-resize": "top_right_corner",
        "not-allowed": "circle",
        "ns-resize": "sb_v_double_arrow",
        "nw-resize": "top_left_corner",
        "pointer": "hand2",
        "s-resize": "bottom_side",
        "se-resize": "bottom_right_corner",  # se == nw, sw == ne
        "sw-resize": "bottom_left_corner",
        "text": "xterm",
        "w-resize": "left_side",
        "wait": "watch",
        None: "none",
    }

    def to_tcl(self):
        return self.cursor_dict[self.cursor]

    @classmethod
    def from_tcl(cls, tcl_value):
        return cls(
            list(cls.cursor_dict.keys())[
                list(cls.cursor_dict.values()).index(tcl_value)
            ]  # crazy thing to get the key by the value, but i don't wanna make 2 dicts
        )

    @classproperty
    def x(cls):
        return get_tcl_interp().tcl_call(int, "winfo", "pointerx", ".")

    @x.setter  # type: ignore
    @update_before
    def x(cls, new_x: int):
        get_tcl_interp().tcl_call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-x",
            new_x,
        )

    @classproperty
    def y(cls):
        return get_tcl_interp().tcl_call(int, "winfo", "pointery", ".")

    @y.setter  # type: ignore
    @update_before
    def y(cls, new_y: int):
        get_tcl_interp().tcl_call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-y",
            new_y,
        )

    @classproperty
    def position(cls):
        return (cls.x(), cls.y())

    @position.setter  # type: ignore
    @update_before
    def position(cls, new_pos: int | Tuple | List) -> None:
        if isinstance(new_pos, (tuple, list)) and len(new_pos) > 1:
            x, y = new_pos
        else:
            x = y = new_pos

        get_tcl_interp().tcl_call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-x",
            x,
            "-y",
            y,
        )