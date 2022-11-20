from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from screeninfo import get_monitors  # type: ignore

from tukaan._misc import Size
from tukaan._tcl import Tcl
from tukaan._utils import classproperty


def mm(amount: float) -> float:
    return round(amount / (Screen.ppi / 25.4), 2)


def cm(amount: float) -> float:
    return round(amount / (Screen.ppi / 2.54), 2)


def inch(amount: float) -> float:
    return round(amount / Screen.ppi, 2)


@dataclass
class ScreenDistance:
    pixels: float

    def __init__(
        self,
        px: float | None = None,
        mm: float | None = None,
        cm: float | None = None,
        inch: float | None = None,
    ) -> None:
        self._ppi = ppi = Screen.ppi

        self.pixels = 0
        if px is not None:
            self.pixels += px
        if mm is not None:
            self.pixels += mm * (ppi * 25.4)
        if cm is not None:
            self.pixels += cm * (ppi * 2.54)
        if inch is not None:
            self.pixels += inch * ppi

    def __to_tcl__(self) -> str:
        return str(self.pixels)

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> ScreenDistance:
        unit = tcl_value[-1]
        value = int(tcl_value[:-1])

        if unit == "c":
            return cls(cm=value)
        if unit == "m":
            return cls(mm=value)
        if unit == "i":
            return cls(inch=value)

        return cls(px=value)

    def __eq__(self, other: ScreenDistance) -> bool:
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels == other.pixels

    def __gt__(self, other: ScreenDistance) -> bool:
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels > other.pixels

    def __lt__(self, other: ScreenDistance) -> bool:
        if not isinstance(other, ScreenDistance):
            raise TypeError

        return self.pixels < other.pixels

    @property
    def px(self) -> float:
        return round(self.pixels, 2)

    @property
    def mm(self) -> float:
        return mm(self.pixels)

    @property
    def cm(self) -> float:
        return cm(self.pixels)

    @property
    def inch(self) -> float:
        return inch(self.pixels)


common_resolution_standards: dict[tuple[int, int], str] = {
    (320, 200): "CGA",
    (320, 240): "QVGA",
    (640, 480): "VGA",
    (768, 576): "PAL",
    (800, 480): "WVGA",
    (800, 600): "SVGA",
    (854, 480): "FWVGA",
    (1024, 600): "WSVGA",
    (1024, 768): "XGA",
    (1280, 1024): "SXGA",
    (1280, 720): "HD 720",
    (1280, 768): "WXGA",
    (1280, 800): "WXGA",
    (1400, 1050): "SXGA+",
    (1600, 1200): "UXGA",
    (1680, 1050): "WSXGA+",
    (1920, 1080): "HD 1080",
    (1920, 1200): "WUXGA",
    (2048, 1080): "2K",
    (2048, 1536): "QXGA",
    (2560, 1600): "WQXGA",
    (2560, 2048): "QSXGA",
}

common_aspect_ratios: dict[float, str] = {
    3 / 2: "3:2",
    4 / 3: "4:3",
    5 / 3: "5:3",
    5 / 4: "5:4",
    16 / 10: "16:10",
    16 / 9: "16:9",
    17 / 9: "17:9",
}

common_color_depths: dict[int, str] = {
    1: "monochrome",
    15: "high color",
    16: "high color",
    24: "true color",
    30: "deep color",
    36: "deep color",
    48: "deep color",
}


class Screen:
    try:
        for monitor in get_monitors():
            if monitor.is_primary:
                _width = monitor.width or 0
                _height = monitor.height or 0
                _mm_width = monitor.width_mm or 0
                _mm_height = monitor.height_mm or 0
    except Exception:
        # FIXME: Use Tcl winfo command, tho it's influenced by dpi :(
        _width = 0
        _height = 0
        _mm_width = 0
        _mm_height = 0

    @classproperty
    def dpi(self) -> float:
        return Tcl.call(float, "winfo", "fpixels", ".", "1i")

    @classproperty
    def ppi(self) -> float:
        screen_diagonal_inch = ((self._mm_width / 25.4) ** 2 + (self._mm_height / 25.4) ** 2) ** 0.5
        screen_diagonal_px = (self._width**2 + self._height**2) ** 0.5

        return screen_diagonal_px / screen_diagonal_inch

    @classproperty
    def width(self) -> ScreenDistance:
        return ScreenDistance(px=self._width)

    @classproperty
    def height(self) -> ScreenDistance:
        return ScreenDistance(px=self._height)

    @classproperty
    def size(self) -> Size:
        return Size(self._width, self._height)

    @classproperty
    def area(self) -> float:
        return self._width * self._height

    @classproperty
    def diagonal(self) -> ScreenDistance:
        return ScreenDistance(px=(self._width**2 + self._height**2) ** 0.5)

    @classproperty
    def color_depth(self) -> int:
        return Tcl.call(int, "winfo", "screendepth", ".")

    @classproperty
    def color_depth_alias(self) -> str:
        try:
            return common_color_depths[self.color_depth]
        except KeyError:
            return ""

    @classproperty
    def aspect_ratio(self) -> str:
        try:
            return common_aspect_ratios[self._width / self._height]
        except KeyError:
            fraction = Fraction(self._width, self._height)  # reduce the ratio
            return f"{fraction.numerator}:{fraction.denominator}"

    @classproperty
    def resolution_standard(self) -> str:
        try:
            return common_resolution_standards[(self._width, self._height)]
        except KeyError:
            return ""
