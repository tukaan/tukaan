from __future__ import annotations

import collections
import re
from typing import Dict, List, Optional, Tuple, Union, cast

# fmt: off
from ._platform import Platform
# fmt: off
from ._utils import (ClassPropertyMetaClass, ColorError, FontError,
                     TukaanError, _flatten, _pairs, classproperty, from_tcl,
                     get_tcl_interp, reversed_dict, to_tcl, update_before)


class HEX:
    @staticmethod
    def to_hex(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def from_hex(hex) -> Tuple[int, int, int]:
        int_value = int(hex.lstrip("#"), 16)
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

        return cast(Tuple[int, int, int], tuple(int(round(x, 0)) for x in (h, s, v)))

    @staticmethod
    def from_hsv(h, s, v) -> Tuple[int, int, int]:
        h, s, v = h / 360, s / 100, v / 100

        if s == 0.0:
            return cast(Tuple[int, int, int], tuple(int(round(x * 255, 0)) for x in (v, v, v)))

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
            (v, p, q)
        ][int(i % 6)]

        return cast(Tuple[int, int, int], tuple(int(round(x * 255, 0)) for x in (r, g, b)))


class CMYK:
    @staticmethod
    def to_cmyk(r, g, b) -> Tuple[int, int, int, int]:
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 100)

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)

        return cast(
            Tuple[int, int, int, int], tuple(int(round(x * 100, 0)) for x in (c, m, y, k))
        )

    @staticmethod
    def from_cmyk(c, m, y, k) -> Tuple[int, int, int]:
        r = (1.0 - (c + k) / 100.0)
        g = (1.0 - (m + k) / 100.0)
        b = (1.0 - (y + k) / 100.0)

        return cast(Tuple[int, int, int], tuple(int(round(x * 255, 0)) for x in (r, g, b)))


# TODO: hsl, yiq
class Color:
    _supported_color_spaces = {"hex", "rgb", "hsv", "cmyk"}

    def __init__(self, color: str | Tuple[int, int, int] | Tuple[int, int, int, int], space: str = "hex") -> None:
        if space == "hex" and isinstance(color, str):
            rgb = HEX.from_hex(color)

        elif space == "rgb" and isinstance(color, tuple) and len(color) == 3:
            rgb = color  # type: ignore

        elif space == "hsv" and isinstance(color, tuple) and len(color) == 3:
            rgb = HSV.from_hsv(*color)

        elif space == "cmyk" and isinstance(color, tuple) and len(color) == 4:
            rgb = CMYK.from_cmyk(*color)

        else:
            raise ColorError(self._what_is_the_problem(color, space))

        self.red, self.green, self.blue = rgb

    def _what_is_the_problem(self, color: str | Tuple[int, int, int] | Tuple[int, int, int, int], space: str) -> str:
        length_dict = {
            "rgb":3,
            "hsv": 3,
            "cmyk": 4
        }

        if space not in self._supported_color_spaces:
            return f"{space!r} is not a supported color space for tukaan.Color."
        elif space == "hex":
            return f"{color!r} is not a valid hexadecimal color name."
        elif space in {"rgb", "hsv", "cmyk"} and not isinstance(color, tuple):
            return f"{color!r} is not a valid {space} color. A tuple is expected."
        elif space in {"rgb", "hsv", "cmyk"} and len(color) != length_dict[space]:
            return f"{color!r} is not a valid {space} color. A tuple with length of {length_dict[space]} is expected."

        return "Not implemented tukaan.Color error."  # shouldn't get here

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


class Clipboard(metaclass=ClassPropertyMetaClass):
    @classmethod
    def __repr__(self) -> str:
        return f"{type(self).__name__}(content={self.get()})"

    @classmethod
    def clear(cls) -> None:
        get_tcl_interp()._tcl_call(None, "clipboard", "clear")

    @classmethod
    def append(cls, content) -> None:
        get_tcl_interp()._tcl_call(None, "clipboard", "append", content)

    @classmethod
    def get(cls) -> str:
        try:
            return get_tcl_interp()._tcl_call(str, "clipboard", "get")
        except TukaanError:
            # implement clipboard image with PIL.ImageGrab.grabclipboard
            return ""

    __str__ = get

    @classmethod
    def set(cls, new_content: str) -> None:
        get_tcl_interp()._tcl_call(None, "clipboard", "clear")
        get_tcl_interp()._tcl_call(None, "clipboard", "append", new_content)

    @classproperty
    def content(cls) -> str:
        return cls.get()

    # "Name "content" already defined on line blablabla"
    @content.setter  # type: ignore
    def content(cls, new_content: str) -> None:
        cls.set(new_content)


class Cursor(
    collections.namedtuple("Cursor", "cursor"), metaclass=ClassPropertyMetaClass
):
    """An object to use cross-platform, and human-understandable cursor names,
    and to get and set the mouse cursor position"""

    _cursor_dict: Dict[Union[str, None], str] = {
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

    _win_cursor_dict: Dict[Union[str, None], str] = {
        "not-allowed": "no",
        "progress": "starting",
        "ne-sw-resize": "size_ne_sw",
        "ns-resize": "size_ns",
        "nw-se-resize": "size_nw_se",
        "wait": "wait",
        "we-resize": "size_we",
    }

    if Platform.system == "Windows":
        _cursor_dict = {**_cursor_dict, **_win_cursor_dict}

    def to_tcl(self) -> str:
        return self._cursor_dict[self.cursor]

    @classmethod
    def from_tcl(cls, tcl_value) -> Cursor:
        return cls(reversed_dict(cls._cursor_dict)[tcl_value])

    @classproperty
    def x(cls) -> int:
        return get_tcl_interp()._tcl_call(int, "winfo", "pointerx", ".")

    @x.setter  # type: ignore
    @update_before
    def x(cls, new_x: int) -> None:
        get_tcl_interp()._tcl_call(
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
    def y(cls) -> int:
        return get_tcl_interp()._tcl_call(int, "winfo", "pointery", ".")

    @y.setter  # type: ignore
    @update_before
    def y(cls, new_y: int) -> None:
        get_tcl_interp()._tcl_call(
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
    def position(cls) -> Tuple[int, int]:
        return (cls.x(), cls.y())

    @position.setter  # type: ignore
    @update_before
    def position(cls, new_pos: int | Tuple[int, int] | List[int]) -> None:
        if isinstance(new_pos, (tuple, list)) and len(new_pos) > 1:
            x, y = new_pos
        elif isinstance(new_pos, int):
            x = y = new_pos

        get_tcl_interp()._tcl_call(
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


class Font(
    collections.namedtuple("Font", "family size bold italic underline strikethrough"),
    metaclass=ClassPropertyMetaClass,
):
    def __new__(
        cls,
        family: str = "default-font",
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> Font:

        if family in cls.presets:
            # small-caption-font -> TkSmallCaptionFont
            family = f"Tk{family.title().replace('-', '')}"

        if family not in cls.families: # presets are already checked
            raise FontError(f"the font family {family!r} is not found, or is not a valid font name.")

        return super(Font, cls).__new__(
            cls, family, size, bold, italic, underline, strikethrough
        )

    def to_tcl(self) -> Tuple:  # i won't write out, and then cast 12 str-s
        font_dict = {
            "-family": self.family,
            "-size": self.size,
            "-weight": "bold" if self.bold else "normal",
            "-slant": "italic" if self.italic else "roman",
            "-underline": self.underline,
            "-overstrike": self.strikethrough,
        }

        return tuple(to_tcl(x) for x in _flatten(font_dict.items()))

    @classmethod
    def from_tcl(cls, tcl_value: Tuple) -> Font:
        types = {
            "family": str,
            "size": int,
            "bold": bool,
            "italic": bool,
            "underline": bool,
            "strikethrough": bool,
        }

        result_dict = {}

        for key, value in _pairs(tcl_value):
            key = key.lstrip("-")

            if key == "weight":
                value = (value == "bold")
                key = "bold"
            elif key == "slant":
                value = (value == "italic")
                key = "italic"
            elif key == "overstrike":
                key = "strikethrough"

            result_dict[key] = from_tcl(types[key], value)

        return cls(**result_dict)

    @classmethod
    def get_families(self, at_prefix: bool = False) -> List[str]:
        result = sorted(set(get_tcl_interp()._tcl_call([str], "font", "families")))
        # i get a way longer list, if not convert it to set. e.g Ubuntu were 3 times
        if at_prefix:
            return result
        return [family for family in result if not family.startswith("@")]

    @classproperty
    def families(self) -> List[str]:
        return self.get_families(True)

    @classproperty
    def presets(self) -> List[str]:
        result = sorted(get_tcl_interp()._tcl_call([str], "font", "names"))

        for index, item in enumerate(result):
            #  TkSmallCaptionFont -> small-caption-font
            result[index] = "-".join(
                re.findall(r".[^A-Z]*", item.replace("Tk", ""))
            ).lower()

        return result

    def measure(self, text: str) -> int:
        return get_tcl_interp()._tcl_call(int, "font", "measure", self, text)

    def metrics(self) -> Dict[str, Union[int, bool]]:
        result = get_tcl_interp()._tcl_call(
            {"-ascent": int, "-descent": int, "-linespace": int, "-fixed": bool},
            "font",
            "metrics",
            self,
        )
        return {key.lstrip("-"): value for key, value in result.items()}



class Screen(metaclass=ClassPropertyMetaClass):
    @classproperty
    def width(cls) -> ScreenDistance:
        width = get_tcl_interp()._tcl_call(int, "winfo", "screenwidth", ".")
        return ScreenDistance(width)

    @classproperty
    def height(cls) -> ScreenDistance:
        height = get_tcl_interp()._tcl_call(int, "winfo", "screenheight", ".")
        return ScreenDistance(height)

    @classproperty
    def size(cls) -> Tuple[ScreenDistance, ScreenDistance]:
        return (cls.width, cls.height)

    @classproperty
    def depth(cls) -> str:
        return get_tcl_interp()._tcl_call(str, "winfo", "screendepth", ".")

    @classproperty
    def dpi(cls) -> float:
        return get_tcl_interp()._tcl_call(float, "winfo", "fpixels", ".", "1i")


class ScreenDistance(collections.namedtuple("ScreenDistance", "distance")):
    """An object to convert between different screen distance units"""

    _tcl_units = {"px": "", "mm": "m", "cm": "c", "m": "c", "inch": "i", "ft": "i"}

    def __new__(cls, distance, unit="px") -> ScreenDistance:
        if unit != "px":
            distance = f"{distance}{cls._tcl_units[unit]}"

            pixels = get_tcl_interp()._tcl_call(float, "winfo", "fpixels", ".", distance)

            if unit == "m":
                pixels *= 100
            elif unit == "ft":
                pixels *= 12
        else:
            pixels = distance

        cls.dpi = Screen.dpi

        return super(ScreenDistance, cls).__new__(cls, pixels)

    def to_tcl(self) -> str:
        return str(self.distance)

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
