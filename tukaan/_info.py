from __future__ import annotations

import platform
from collections import namedtuple
from datetime import datetime
from fractions import Fraction

import _tkinter as tk
import psutil
from screeninfo import get_monitors

if platform.system() == "Linux":
    import distro

from ._units import MemoryUnit, ScreenDistance

OsVersion = namedtuple("OsVersion", ["major", "minor", "build"])
Version = namedtuple("Version", ["major", "minor", "patchlevel"])


class _Platform:
    arch: tuple[str, str] = platform.architecture()
    node: str = platform.node()
    os: str = {"Linux": "Linux", "Windows": "Windows", "Darwin": "macOS"}[platform.system()]
    py_version: tuple[int, int, int] = Version(*map(int, platform.python_version_tuple()))
    tk_version = Version(*map(int, tk.TK_VERSION.split(".")), 0)
    release: str = platform.release()

    @property
    def os_version(self) -> tuple[str, str, str]:
        if self.os == "Linux":
            return OsVersion(*distro.version_parts())
        elif self.os == "Windows":
            return OsVersion(*platform.version().split("."))
        elif self.os == "macOS":
            return OsVersion(*platform.mac_ver()[0].split("."), 0)

    @property
    def os_distro(self) -> str | None:
        if self.os == "Linux":
            return distro.name()

    @property
    def os_codename(self) -> str:
        if self.os == "Linux":
            return distro.codename()

    @property
    def uptime(self):
        return datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    @property
    def win_sys(self) -> str:
        from ._utils import get_tcl_interp

        return {"win32": "DWM", "x11": "X11", "aqua": "Quartz"}[
            get_tcl_interp()._tcl_call(str, "tk", "windowingsystem")
        ]

    @property
    def tcl_version(self) -> str:
        from ._utils import get_tcl_interp

        return Version(*map(int, get_tcl_interp()._tcl_call(str, "info", "patchlevel").split(".")))

    @property
    def dark_mode(self):
        if self.os == "Windows":
            from winreg import HKEY_CURRENT_USER, QueryValueEx, OpenKey

            try:
                key = OpenKey(HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                result = QueryValueEx(key, "AppsUseLightTheme")[0]
            except FileNotFoundError:
                return False
            
            return bool(result)
        
        elif self.os == "macOS":
            from subprocess import Popen, PIPE
            
            p = Popen(["defaults", "read", "-g", "AppleInterfaceStyle"], stdout=PIPE, stderr=PIPE)
            return "Dark" in p.communicate()[0]
        
        return False


class _Machine:
    cpu: str = platform.processor()
    machine: str = platform.machine()


class _Memory:
    _root_path = {"Linux": "/", "Darwin": "/", "Windows": "C:\\"}[platform.system()]

    @property
    def ram_size(self):
        return MemoryUnit(psutil.virtual_memory().total)
    
    @property
    def ram_available(self):
        return MemoryUnit(psutil.virtual_memory().available)

    @property
    def ram_used(self):
        return MemoryUnit(psutil.virtual_memory().used)

    @property
    def swap_size(self):
        return MemoryUnit(psutil.swap_memory().total)

    @property
    def swap_free(self):
        return MemoryUnit(psutil.swap_memory().free)

    @property
    def swap_used(self):
        return MemoryUnit(psutil.swap_memory().used)

    @property
    def drive_size(self):
        return MemoryUnit(psutil.disk_usage(self._root_path).total)

    @property
    def drive_space_free(self):
        return MemoryUnit(psutil.disk_usage(self._root_path).free)

    @property
    def drive_space_used(self):
        return MemoryUnit(psutil.disk_usage(self._root_path).used)

    def _get_primary_drive(self):
        for drive in psutil.disk_partitions():
            if drive.mountpoint in {"/", "C:\\"}:
                return drive

    @property
    def drive_filesystem(self):
        return self._get_primary_drive().fstype

    @property
    def drive_device(self):
        return self._get_primary_drive().device


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
    _width = None
    _height = None
    _mm_width = None
    _mm_height = None

    for _monitor in get_monitors():
        if _monitor.is_primary:
            _width = _monitor.width
            _height = _monitor.height
            _mm_width = _monitor.width_mm
            _mm_height = _monitor.height_mm

    @property
    def width(cls):
        return ScreenDistance(px=cls._width)

    @property
    def height(cls):
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
    def diagonal(self) -> int:
        return ScreenDistance(px=(self._width**2 + self._height**2) ** 0.5)

    @property
    def color_depth(self) -> int:
        from ._utils import get_tcl_interp

        return get_tcl_interp()._tcl_call(int, "winfo", "screendepth", ".")

    @property
    def color_depth_alias(self) -> str:
        try:
            return common_color_depths[self.color_depth]
        except KeyError:
            return ""

    @property
    def dpi(self) -> float:
        from ._utils import get_tcl_interp

        return get_tcl_interp()._tcl_call(float, "winfo", "fpixels", ".", "1i")

    @property
    def ppi(self) -> float:
        screen_diagonal_inch = ((self._mm_width / 25.4) ** 2 + (self._mm_height / 25.4) ** 2) ** 0.5
        screen_diagonal_px = (self._width**2 + self._height**2) ** 0.5

        return screen_diagonal_px / screen_diagonal_inch


# Instantiate them
Machine = _Machine()
Memory = _Memory()
Platform = _Platform()
Screen = _Screen()
