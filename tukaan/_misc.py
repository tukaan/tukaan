from __future__ import annotations

import collections
from abc import ABC, abstractstaticmethod
from fractions import Fraction
from typing import Callable, Tuple, cast

from PIL import ImageGrab  # type: ignore

from ._info import System
from ._tcl import Tcl
from ._utils import ClassPropertyMetaClass, classproperty, reversed_dict
from .exceptions import TclError

intround: Callable[[float], int] = lambda x: int(round(x, 0))
round4: Callable[[float], float] = lambda x: round(x, 4)


Bbox = collections.namedtuple("Bbox", ["x", "y", "width", "height"])


class Clipboard(metaclass=ClassPropertyMetaClass):
    @classmethod
    def __repr__(cls) -> str:
        return f"{type(cls).__name__}(content={cls.get()})"

    @classmethod
    def clear(cls) -> None:
        Tcl.call(None, "clipboard", "clear")

    @classmethod
    def append(cls, content) -> None:
        Tcl.call(None, "clipboard", "append", content)

    def __add__(self, content) -> Clipboard:
        self.append(content)
        return self

    @classmethod
    def get(cls) -> str | None:
        try:
            return Tcl.call(str, "clipboard", "get")
        except TclError:
            try:
                return ImageGrab.grabclipboard()
            except NotImplementedError:
                # grabclipboard() is macOS and Windows only
                return None

    @classmethod
    def set(cls, new_content: str) -> None:
        Tcl.call(None, "clipboard", "clear")
        Tcl.call(None, "clipboard", "append", new_content)

    @classproperty
    def content(cls) -> str:
        return cls.get()

    @content.setter
    def content(cls, new_content: str) -> None:
        cls.set(new_content)


class Cursor(collections.namedtuple("Cursor", "cursor"), metaclass=ClassPropertyMetaClass):
    _cursor_dict: dict[str | None, str] = {
        "crosshair": "crosshair",
        "default": "arrow",
        "e-resize": "right_side",
        "help": "question_arrow",
        "move": "fleur",
        "n-resize": "top_side",
        "ne-sw-resize": "top_right_corner",
        "not-allowed": "circle",
        "ns-resize": "sb_v_double_arrow",
        "nw-se-resize": "top_left_corner",
        "pointer": "hand2",
        "progress": "arrow",  # for cross-platform compatibility
        "s-resize": "bottom_side",
        "text": "xterm",
        "w-resize": "left_side",
        "wait": "watch",
        "we-resize": "sb_h_double_arrow",
        None: "none",
    }

    _win_cursor_dict: dict[str | None, str] = {
        "not-allowed": "no",
        "progress": "starting",
        "ne-sw-resize": "size_ne_sw",
        "ns-resize": "size_ns",
        "nw-se-resize": "size_nw_se",
        "wait": "wait",
        "we-resize": "size_we",
    }

    if System.os == "Windows":
        _cursor_dict = {**_cursor_dict, **_win_cursor_dict}

    def to_tcl(self) -> str:
        return self._cursor_dict[self.cursor]

    @classmethod
    def from_tcl(cls, tcl_value: str) -> Cursor:
        return cls(reversed_dict(cls._cursor_dict)[tcl_value])

    @classproperty
    def x(cls) -> int:
        return Tcl.call(int, "winfo", "pointerx", ".")

    @x.setter
    @Tcl.update_after
    def x(cls, new_x: int) -> None:
        Tcl.call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-x",
            new_x,
            "-y",
            cls.y,
        )

    @classproperty
    def y(cls) -> int:
        return Tcl.call(int, "winfo", "pointery", ".")

    @y.setter
    @Tcl.update_after
    def y(cls, new_y: int) -> None:
        Tcl.call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-y",
            new_y,
            "-x",
            cls.x,
        )

    @classproperty
    def position(cls) -> tuple[int, int]:
        return (cls.x, cls.y)

    @position.setter
    @Tcl.update_after
    def position(cls, new_pos: int | tuple[int, int] | list[int]) -> None:
        if isinstance(new_pos, (tuple, list)) and len(new_pos) > 1:
            x, y = new_pos
        elif isinstance(new_pos, int):
            x = y = new_pos
        else:
            raise RuntimeError

        Tcl.call(None, "event", "generate", ".", "<Motion>", "-warp", "1", "-x", x, "-y", y)


class Color:
    def __init__(self, red, green, blue) -> None:
        self.red = red
        self.green = green
        self.blue = blue

    def __repr__(self) -> str:
        return f"{type(self).__name__}(red={self.red}, green={self.green}," + f" blue={self.blue})"

    __str__ = __repr__

    def __to_tcl__(self) -> str:
        return self.hex

    @classmethod
    def __from_tcl__(cls, tcl_value) -> Color:
        return cls(tcl_value)

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
    def hex(self) -> str:
        return hex._to(self.red, self.green, self.blue)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def hsv(self) -> tuple:
        return hsv._to(self.red, self.green, self.blue)

    @property
    def hsl(self) -> tuple:
        return hsl._to(self.red, self.green, self.blue)

    @property
    def cmyk(self) -> tuple:
        return cmyk._to(self.red, self.green, self.blue)


class ColorFactory(ABC):
    @abstractstaticmethod
    def _to(r, g, b):
        ...

    @abstractstaticmethod
    def _from(color) -> tuple[int, int, int]:
        ...


class rgb(ColorFactory):
    def __new__(self, r, g, b):
        return Color(r, g, b)

    def _to(r, g, b) -> str:
        return r, g, b

    def _from(r, g, b) -> tuple[int, ...]:
        return r, g, b


class hex(ColorFactory):
    def __new__(cls, string):
        return Color(cls._from(string))

    def _to(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    def _from(string) -> tuple[int, ...]:
        int_value = int(hex.lstrip("#"), 16)
        return int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF


class hsl(ColorFactory):
    def __new__(cls, h, s, l):
        return Color(cls._from(h, s, l))

    def _to(r, g, b) -> tuple[int, ...]:
        r, g, b = r / 255, g / 255, b / 255
        min_value = min(r, g, b)
        max_value = max(r, g, b)

        l = (min_value + max_value) / 2

        if min_value == max_value:
            return (0, 0, intround(l * 100))

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

        return tuple(intround(x) for x in (h * 60, s * 100, l * 100))

    def _from(h, s, l) -> tuple[int, ...]:
        h, s, l = h / 360, s / 100, l / 100

        if s == 0.0:
            return (intround(l * 255),) * 3

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

        return tuple(intround(x) for x in (r * 255, g * 255, b * 255))


class hsv:
    def __new__(cls, h, s, v):
        return Color(cls._from(h, s, v))

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

        return tuple(intround(x) for x in (h, s, v))

    def _from(h, s, v) -> tuple[int, ...]:
        h, s, v = h / 360, s / 100, v / 100

        if s == 0.0:
            return cast(Tuple[int, ...], tuple(intround(x * 255) for x in (v, v, v)))

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

        return cast(Tuple[int, ...], tuple(intround(x * 255) for x in (r, g, b)))


class cmyk(ColorFactory):
    def __new__(cls, c, m, y, k):
        return Color(cls._from(c, m, y, k))

    def _to(r, g, b) -> tuple[int, ...]:
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 100)

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = c - k
        m = m - k
        y = y - k

        return tuple(intround(x * 100) for x in (c, m, y, k))

    def _from(c, m, y, k) -> tuple[int, ...]:
        c = c / 100.0
        m = m / 100.0
        y = y / 100.0
        k = k / 100.0

        r = 255.0 - ((min(1.0, c * (1.0 - k) + k)) * 255.0)
        g = 255.0 - ((min(1.0, m * (1.0 - k) + k)) * 255.0)
        b = 255.0 - ((min(1.0, y * (1.0 - k) + k)) * 255.0)

        return tuple(intround(x) for x in (r, g, b))
