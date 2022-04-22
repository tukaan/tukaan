from __future__ import annotations

import platform
from fractions import Fraction

import _tkinter as tk
import psutil
from screeninfo import get_monitors  # type: ignore

from ._structures import OsVersion, Position, Version
from .exceptions import TclError

if platform.system() == "Linux":
    import distro  # type: ignore


class _System:
    arch: tuple[str, str] = platform.architecture()
    node: str = platform.node()
    os: str = {"Linux": "Linux", "Windows": "Windows", "Darwin": "macOS"}[platform.system()]
    py_version: tuple[int, int, int] = Version(*map(int, platform.python_version_tuple()))
    release: str = platform.release()
    tk_version = Version(*map(int, tk.TK_VERSION.split(".")), 0)

    @property
    def os_version(self) -> OsVersion | None:
        if self.os == "Linux":
            return OsVersion(*distro.version_parts())
        elif self.os == "Windows":
            return OsVersion(*platform.version().split("."))
        elif self.os == "macOS":
            return OsVersion(*platform.mac_ver()[0].split("."), 0)

        return None

    @property
    def os_distro(self) -> str | None:
        if self.os == "Linux":
            return distro.name()
        return None

    @property
    def os_codename(self) -> str | None:
        if self.os == "Linux":
            return distro.codename()
        return None

    @property
    def win_sys(self) -> str:
        from ._tcl import Tcl

        return {"win32": "DWM", "x11": "X11", "aqua": "Quartz"}[Tcl.windowing_system]

    @property
    def tcl_version(self) -> Version:
        from ._tcl import Tcl

        return Version(*map(int, Tcl.version.split(".")))

    @property
    def dark_mode(self):
        if self.os == "Windows":
            from winreg import HKEY_CURRENT_USER, OpenKey, QueryValueEx

            try:
                key = OpenKey(
                    HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                result = QueryValueEx(key, "AppsUseLightTheme")[0]
            except FileNotFoundError:
                return False

            return bool(result)

        elif self.os == "macOS":
            from subprocess import PIPE, Popen

            p = Popen(["defaults", "read", "-g", "AppleInterfaceStyle"], stdout=PIPE, stderr=PIPE)
            return "dark" in p.communicate()[0].lower()

        return False


class _Machine:
    cpu: str = platform.processor()
    machine: str = platform.machine()


common_resolution_standards = {
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
    (320, 200): "CGA",
    (320, 240): "QVGA",
    (640, 480): "VGA",
    (768, 576): "PAL",
    (800, 480): "WVGA",
    (800, 600): "SVGA",
    (854, 480): "FWVGA",
}

common_aspect_ratios = {
    16 / 10: "16:10",
    16 / 9: "16:9",
    17 / 9: "17:9",
    3 / 2: "3:2",
    4 / 3: "4:3",
    5 / 3: "5:3",
    5 / 4: "5:4",
}

common_color_depths = {
    1: "monochrome",
    15: "high color",
    16: "high color",
    24: "true color",
    30: "deep color",
    36: "deep color",
    48: "deep color",
}


class _Screen:
    _width: int = 0
    _height: int = 0
    _mm_width: int = 0
    _mm_height: int = 0

    for _monitor in get_monitors():
        if _monitor.is_primary:
            _width = _monitor.width or 0
            _height = _monitor.height or 0
            _mm_width = _monitor.width_mm or 0
            _mm_height = _monitor.height_mm or 0

    @property
    def width(cls):
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=cls._width)

    @property
    def height(cls):
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=cls._height)

    @property
    def size(self):
        return (self._width, self._height)

    @property
    def area(self):
        return self._width * self._height

    @property
    def aspect_ratio(self) -> str:
        try:
            return common_aspect_ratios[self._width / self._height]
        except KeyError:
            fraction = Fraction(self._width, self._height)  # reduce the ratio
            return f"{fraction.numerator}:{fraction.denominator}"

    @property
    def resolution_standard(self) -> str:
        try:
            return common_resolution_standards[(self._width, self._height)]
        except KeyError:
            return ""

    @property
    def diagonal(self) -> ScreenDistance:
        from .screen_distance import ScreenDistance

        return ScreenDistance(px=(self._width**2 + self._height**2) ** 0.5)

    @property
    def color_depth(self) -> int:
        from ._tcl import Tcl

        return Tcl.call(int, "winfo", "screendepth", ".")

    @property
    def color_depth_alias(self) -> str:
        try:
            return common_color_depths[self.color_depth]
        except KeyError:
            return ""

    @property
    def dpi(self) -> float:
        from ._tcl import Tcl

        return Tcl.call(float, "winfo", "fpixels", ".", "1i")

    @property
    def ppi(self) -> float:
        screen_diagonal_inch = ((self._mm_width / 25.4) ** 2 + (self._mm_height / 25.4) ** 2) ** 0.5
        screen_diagonal_px = (self._width**2 + self._height**2) ** 0.5

        return screen_diagonal_px / screen_diagonal_inch


class _Clipboard:
    def __repr__(self) -> str:
        return f"<tukaan.Clipboard; content: {self.get()}>"

    def clear(self) -> None:
        from ._tcl import Tcl

        Tcl.call(None, "clipboard", "clear")

    def append(self, content) -> None:
        from ._tcl import Tcl

        Tcl.call(None, "clipboard", "append", content)

    def __add__(self, content) -> _Clipboard:
        self.append(content)
        return self

    def get(self) -> str | None:
        from ._tcl import Tcl

        try:
            return Tcl.call(str, "clipboard", "get")
        except TclError:
            return None

    def set(self, new_content: str) -> None:
        self.clear()
        self.append(new_content)

    @property
    def content(self) -> str:
        return self.get()

    @content.setter
    def content(self, new_content: str) -> None:
        self.set(new_content)


class _Pointer:
    def __repr__(self) -> str:
        return f"<tukaan.Pointer; position: {tuple(self.position)}>"

    @property
    def x(cls) -> int:
        from ._tcl import Tcl

        return Tcl.call(int, "winfo", "pointerx", ".")

    @property
    def y(cls) -> int:
        from ._tcl import Tcl

        return Tcl.call(int, "winfo", "pointery", ".")

    @property
    def position(cls) -> tuple[int, int]:
        return Position(cls.x, cls.y)


# Instantiate them
Clipboard = _Clipboard()
Machine = _Machine()
Pointer = _Pointer()
Screen = _Screen()
System = _System()
