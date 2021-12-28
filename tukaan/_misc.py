from __future__ import annotations

import collections
import re
from typing import Callable, Tuple, cast

from ._platform import Platform
from ._utils import (
    ClassPropertyMetaClass,
    _flatten,
    _fonts,
    _pairs,
    classproperty,
    counts,
    from_tcl,
    get_tcl_interp,
    py_to_tcl_arguments,
    reversed_dict,
    to_tcl,
    update_after,
)
from .exceptions import ColorError, TclError

intround: Callable[[float], int] = lambda x: int(round(x, 0))
round4: Callable[[float], float] = lambda x: round(x, 4)


class HEX:
    @staticmethod
    def to_hex(r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def from_hex(hex) -> tuple[int, ...]:
        int_value = int(hex.lstrip("#"), 16)
        return cast(Tuple[int, ...], (int_value >> 16, int_value >> 8 & 0xFF, int_value & 0xFF))


class HSV:
    @staticmethod
    def to_hsv(r, g, b) -> tuple[int, ...]:
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

        return cast(Tuple[int, ...], tuple(intround(x) for x in (h, s, v)))

    @staticmethod
    def from_hsv(h, s, v) -> tuple[int, ...]:
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


class CMYK:
    @staticmethod
    def to_cmyk(r, g, b) -> tuple[int, ...]:
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 100)

        c, m, y = (1 - x / 255 for x in (r, g, b))

        k = min(c, m, y)
        c = c - k
        m = m - k
        y = y - k

        return cast(Tuple[int, ...], tuple(intround(x * 100) for x in (c, m, y, k)))

    @staticmethod
    def from_cmyk(c, m, y, k) -> tuple[int, ...]:
        c = c / 100.0
        m = m / 100.0
        y = y / 100.0
        k = k / 100.0

        r = 255.0 - ((min(1.0, c * (1.0 - k) + k)) * 255.0)
        g = 255.0 - ((min(1.0, m * (1.0 - k) + k)) * 255.0)
        b = 255.0 - ((min(1.0, y * (1.0 - k) + k)) * 255.0)

        return cast(Tuple[int, ...], tuple(intround(x) for x in (r, g, b)))


# TODO: hsl, yiq
class Color:
    _supported_color_spaces = {"hex", "rgb", "hsv", "cmyk"}
    red: int
    green: int
    blue: int

    def __init__(self, color: tuple, space: str = "rgb") -> None:
        try:
            if space == "hex":
                if not re.match(r"^#[0-9a-fA-F]{6}$", color):
                    raise ColorError
                self.red, self.green, self.blue = HEX.from_hex(color)

            elif space == "rgb":
                if len(color) != 3 or color < (0, 0, 0) or color > (255, 255, 255):
                    raise ColorError
                self.red, self.green, self.blue = color

            elif space == "hsv":
                if len(color) != 3 or color < (0, 0, 0) or color > (360, 100, 100):
                    raise ColorError
                self.red, self.green, self.blue = HSV.from_hsv(*color)

            elif space == "cmyk":
                if len(color) != 4 or color < (0, 0, 0, 0) or color > (100, 100, 100, 100):
                    raise ColorError
                self.red, self.green, self.blue = CMYK.from_cmyk(*color)

            else:
                raise ColorError
        except (ValueError, ColorError):
            raise ColorError(self._what_is_the_problem(color, space)) from None

    def _what_is_the_problem(self, color: str | tuple[int, ...], space: str) -> str:
        length_dict = {"rgb": 3, "hsv": 3, "cmyk": 4}

        if space not in self._supported_color_spaces:
            return f"{space!r} is not a supported color space for tukaan.Color."

        if space == "hex":
            return f"{color!r} is not a valid hexadecimal color code."

        if space in {"rgb", "hsv", "cmyk"}:
            if not isinstance(color, tuple):
                return f"{color!r} is not a valid {space} color. A tuple is expected."

            else:
                color_passed, expected_length = "", ""

                if len(color) in length_dict.values():

                    if len(color) == 4 and (0, 0, 0, 0) <= color <= (
                        100,
                        100,
                        100,
                        100,
                    ):
                        color_space = "a cmyk"

                    elif len(color) == 3 and (0, 0, 0) <= color <= (255, 100, 100):
                        color_space = "either a rgb or a hsv"

                    elif len(color) == 3 and (0, 0, 0) <= color <= (255, 255, 255):
                        color_space = "a rgb"

                    elif len(color) == 3 and (0, 0, 0) <= color <= (360, 100, 100):
                        color_space = "a hsv"

                    else:
                        color_space = "an invalid"

                    color_passed = f" You passed in {color_space} color."

                if len(color) != length_dict[space]:
                    expected_length = f"A tuple with length of {length_dict[space]} is expected."

                return f"{color!r} is not a valid {space} color." + expected_length + color_passed

        return "Not implemented tukaan.Color error."  # shouldn't get here

    def __repr__(self) -> str:
        return f"{type(self).__name__}(red={self.red}, green={self.green}," + f" blue={self.blue})"

    def to_tcl(self) -> str:
        return self.hex

    __str__ = to_tcl

    @classmethod
    def from_tcl(cls, tcl_value) -> Color:
        return cls(tcl_value)

    def invert(self) -> Color:
        self.red = 255 - self.red
        self.green = 255 - self.green
        self.blue = 255 - self.blue

        return self

    @property
    def is_dark(self):
        # https://www.w3schools.com/lib/w3color.js line 82
        return ((self.red * 299 + self.green * 587 + self.blue * 114) / 1000) < 128

    @property
    def hex(self) -> str:
        return HEX.to_hex(self.red, self.green, self.blue)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def hsv(self) -> tuple:
        return HSV.to_hsv(self.red, self.green, self.blue)

    @property
    def cmyk(self) -> tuple:
        return CMYK.to_cmyk(self.red, self.green, self.blue)


class Clipboard(metaclass=ClassPropertyMetaClass):
    @classmethod
    def __repr__(cls) -> str:
        return f"{type(cls).__name__}(content={cls.get()})"

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
        except TclError:
            # implement clipboard image with PIL.ImageGrab.grabclipboard
            return ""

    @classmethod
    def set(cls, new_content: str) -> None:
        get_tcl_interp()._tcl_call(None, "clipboard", "clear")
        get_tcl_interp()._tcl_call(None, "clipboard", "append", new_content)

    @classproperty
    def content(cls) -> str:
        return cls.get()

    @content.setter
    def content(cls, new_content: str) -> None:
        cls.set(new_content)


class Cursor(collections.namedtuple("Cursor", "cursor"), metaclass=ClassPropertyMetaClass):
    """An object to use cross-platform, and human-understandable cursor names,
    and to get and set the mouse cursor position"""

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

    if Platform.system == "Windows":
        _cursor_dict = {**_cursor_dict, **_win_cursor_dict}

    def to_tcl(self) -> str:
        return self._cursor_dict[self.cursor]

    @classmethod
    def from_tcl(cls, tcl_value: str) -> Cursor:
        return cls(reversed_dict(cls._cursor_dict)[tcl_value])

    @classproperty
    def x(cls) -> int:
        return get_tcl_interp()._tcl_call(int, "winfo", "pointerx", ".")

    @x.setter
    @update_after
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
            "-y",
            cls.y,
        )

    @classproperty
    def y(cls) -> int:
        return get_tcl_interp()._tcl_call(int, "winfo", "pointery", ".")

    @y.setter
    @update_after
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
            "-x",
            cls.x,
        )

    @classproperty
    def position(cls) -> tuple[int, int]:
        return (cls.x, cls.y)

    @position.setter
    @update_after
    def position(cls, new_pos: int | tuple[int, int] | list[int]) -> None:
        if isinstance(new_pos, (tuple, list)) and len(new_pos) > 1:
            x, y = new_pos
        elif isinstance(new_pos, int):
            x = y = new_pos
        else:
            raise RuntimeError

        get_tcl_interp()._tcl_call(
            None, "event", "generate", ".", "<Motion>", "-warp", "1", "-x", x, "-y", y
        )


_preset_fonts = {
    "TkCaptionFont",
    "TkDefaultFont",
    "TkFixedFont",
    "TkHeadingFont",
    "TkIconFont",
    "TkMenuFont",
    "TkSmallCaptionFont",
    "TkTextFont",
    "TkTooltipFont",
}


class Font(metaclass=ClassPropertyMetaClass):
    def __new__(
        cls,
        family: str = "TkDefaultFont",
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> Font | NamedFont:
        _description = {
            "family": family,
            "size": size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "strikethrough": strikethrough,
        }

        if not issubclass(cls, NamedFont):
            try:
                get_tcl_interp()._tcl_call(None, "font", "configure", family)
            except TclError:
                pass
            else:
                return NamedFont(**_description)

        return super(Font, cls).__new__(cls)

    def __init__(
        self,
        family: str = "TkDefaultFont",
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ):

        self._description = {
            "family": family,
            "size": size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "strikethrough": strikethrough,
        }

        print("create")

    def to_tcl(self) -> tuple[str | int | bool, ...]:
        font_dict = {
            "-family": self._description["family"],
            "-size": self._description["size"],
            "-weight": "bold" if self._description["bold"] else "normal",
            "-slant": "italic" if self._description["italic"] else "roman",
            "-underline": self._description["underline"],
            "-overstrike": self._description["strikethrough"],
        }

        return tuple(to_tcl(x) for x in _flatten(font_dict.items()))

    @classmethod
    def from_tcl(cls, tcl_value):
        if tcl_value in _preset_fonts:
            return NamedFont(family=tcl_value)

        if tcl_value in _fonts:
            return _fonts[tcl_value]

        tcl_value = from_tcl((str,), tcl_value)

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
                value = value == "bold"
                key = "bold"
            elif key == "slant":
                value = value == "italic"
                key = "italic"
            elif key == "overstrike":
                key = "strikethrough"

            result_dict[key] = from_tcl(types[key], value)

        return cls(**result_dict)

    def anonym_copy(self):
        return Font(**self._description)

    def named_copy(self):
        return NamedFont(**self._description)

    def getter(self, type_spec, option):
        return get_tcl_interp()._tcl_call(type_spec, "font", "actual", self, f"-{option}")

    @property
    def properties(self):
        return self._description

    @property
    def family(self):
        return self.getter(str, "family")

    @property
    def size(self):
        return self.getter(int, "size")

    @property
    def bold(self):
        return self.getter(str, "weight") == "bold"

    @property
    def italic(self):
        return self.getter(str, "slant") == "italic"

    @property
    def underline(self):
        return self.getter(bool, "underline")

    @property
    def strikethrough(self):
        return self.getter(bool, "overstrike")

    @classproperty
    def named_fonts(cls):
        return get_tcl_interp()._tcl_call((Font,), "font", "names")

    @classproperty
    def families(cls):
        return list(set(get_tcl_interp()._tcl_call([str], "font", "families"))).sort()

    def measure(self, text: str) -> int:
        return get_tcl_interp()._tcl_call(int, "font", "measure", self, text)

    @property
    def metrics(self) -> dict[str, int | bool]:
        result = get_tcl_interp()._tcl_call(
            {"-ascent": int, "-descent": int, "-linespace": int, "-fixed": bool},
            "font",
            "metrics",
            self,
        )
        return {key.lstrip("-"): value for key, value in result.items()}


class NamedFont(Font):
    def __init__(
        self,
        family: str = "TkDefaultFont",
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        _name=None,
    ):
        if _name:
            self._name = _name
        elif family in _preset_fonts:
            self._name = family
        else:
            self._name = f"tukaan_font_{next(counts['fonts'])}"
        _fonts[self._name] = self

        args = py_to_tcl_arguments(
            family=family,
            size=size,
            weight="bold" if bold else "normal",
            slant="italic" if italic else "roman",
            underline=underline,
            overstrike=strikethrough,
        )

        try:
            get_tcl_interp()._tcl_call(None, "font", "create", self._name, *args)
        except TclError:
            # font already exists in tcl
            get_tcl_interp()._tcl_call(None, "font", "configure", self._name, *args)

        super().__init__(self._name)

    def __repr__(self):
        return f"<tukaan.NamedFont object: name={self._name!r}>"

    def to_tcl(self):
        return self._name

    def setter(self, option, value):
        get_tcl_interp()._tcl_call(None, "font", "configure", self._name, f"-{option}", value)

    @Font.family.setter
    def family(self, value):
        return self.setter("family", value)

    @Font.size.setter
    def size(self, value):
        return self.setter("size", value)

    @Font.bold.setter
    def bold(self, value):
        return self.setter("weight", "bold" if value else "normal")

    @Font.italic.setter
    def italic(self, value):
        return self.setter("slant", "italic" if value else "roman")

    @Font.underline.setter
    def underline(self, value):
        return self.setter("underline", value)

    @Font.strikethrough.setter
    def strikethrough(self, value):
        return self.setter("overstrike", value)

    def delete(self):
        get_tcl_interp()._tcl_call(None, "font", "delete", self._name)
        del _fonts[self._name]


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
    def size(cls) -> tuple[ScreenDistance, ScreenDistance]:
        return (cls.width, cls.height)

    @classproperty
    def depth(cls) -> str:
        return get_tcl_interp()._tcl_call(str, "winfo", "screendepth", ".")

    @classproperty
    def dpi(cls) -> float:
        return get_tcl_interp()._tcl_call(float, "winfo", "fpixels", ".", "1i")

    def __str__(self) -> str:
        return f"{self.width.px};{self.height.px}"


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
            pixels = float(distance)

        cls.dpi = Screen.dpi

        return super(ScreenDistance, cls).__new__(cls, pixels)  # type: ignore

    def __repr__(self) -> str:
        return f"{type(self).__name__}(distance={self.distance}px))"

    def __int__(self):
        return intround(self.distance)

    def __float__(self):
        return round4(self.distance)

    def to_tcl(self) -> str:
        return str(self.distance)

    __str__ = to_tcl

    @classmethod
    def from_tcl(cls, tcl_value: int) -> ScreenDistance:
        return cls(tcl_value)

    @property
    def px(self) -> float:
        return round4(self.distance)

    @property
    def mm(self) -> float:
        return round4(self.distance / (self.dpi / 25.4))

    @property
    def cm(self) -> float:
        return round4(self.distance / (self.dpi / 2.54))

    @property
    def m(self) -> float:
        return round4(self.distance / (self.dpi / 0.0254))

    @property
    def inch(self) -> float:
        return round4(self.distance / self.dpi)

    @property
    def ft(self) -> float:
        return round4(self.distance / (self.dpi * 12))
