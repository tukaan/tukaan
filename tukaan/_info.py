from __future__ import annotations

import platform
import sys
from fractions import Fraction

import _tkinter as tk
from screeninfo import get_monitors  # type: ignore

from ._behaviour import classproperty
from ._data import Position, Size, Version
from .exceptions import TclError


class System:
    try:
        os = {"linux": "Linux", "win32": "Windows", "darwin": "macOS"}[sys.platform]
    except KeyError:
        os = sys.platform

    py_version = Version(*map(int, platform.python_version_tuple()))
    tk_version = Version(*map(int, tk.TK_VERSION.split(".")[:2]), None)  # type: ignore

    @classproperty
    def tcl_version(self) -> Version:
        from ._tcl import Tcl

        assert Tcl.version is not None
        return Version(*map(int, Tcl.version.split(".")))

    # @classproperty
    # def win_sys(self) -> str:
    #     from ._tcl import Tcl
    #     assert Tcl.windowing_system is not None
    #
    #     return {"win32": "Win32", "x11": "X11", "aqua": "Quartz"}[Tcl.windowing_system]


class Clipboard:
    def __repr__(self) -> str:
        return f"<tukaan.Clipboard; content: {self.paste()}>"

    def clear(self) -> None:
        from ._tcl import Tcl

        Tcl.call(None, "clipboard", "clear")

    def append(self, content: str) -> None:
        from ._tcl import Tcl

        Tcl.call(None, "clipboard", "append", content)

    def paste(self) -> str | None:
        from ._tcl import Tcl

        try:
            return Tcl.call(str, "clipboard", "get")
        except TclError:
            return None

    def copy(self, content: str) -> None:
        from ._tcl import Tcl

        Tcl.call(None, "clipboard", "clear")
        Tcl.call(None, "clipboard", "append", content)


class Pointer:
    def __repr__(self) -> str:
        return f"<tukaan.Pointer; position: {tuple(self.position)}>"

    @classproperty
    def x(self) -> int:
        from ._tcl import Tcl

        return Tcl.call(int, "winfo", "pointerx", ".")

    @classproperty
    def y(self) -> int:
        from ._tcl import Tcl

        return Tcl.call(int, "winfo", "pointery", ".")

    @classproperty
    def position(self) -> tuple[int, int]:
        return Position(self.x, self.y)


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
        from ._tcl import Tcl

        return Tcl.call(float, "winfo", "fpixels", ".", "1i")

    @classproperty
    def ppi(self) -> float:
        screen_diagonal_inch = ((self._mm_width / 25.4) ** 2 + (self._mm_height / 25.4) ** 2) ** 0.5
        screen_diagonal_px = (self._width**2 + self._height**2) ** 0.5

        return screen_diagonal_px / screen_diagonal_inch

    @classproperty
    def width(self):
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=self._width)

    @classproperty
    def height(self):
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=self._height)

    @classproperty
    def size(self) -> Size:
        return Size(self._width, self._height)

    @classproperty
    def area(self) -> float:
        return self._width * self._height

    @classproperty
    def diagonal(self):
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=(self._width**2 + self._height**2) ** 0.5)

    @classproperty
    def color_depth(self) -> int:
        from ._tcl import Tcl

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
