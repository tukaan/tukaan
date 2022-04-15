from abc import ABC, abstractclassmethod

from tukaan._info import System
from tukaan._tcl import Tcl
from tukaan._utils import mac_only, windows_only


class Theme(ABC):
    @abstractclassmethod
    def _use(cls):
        pass


class ClamTheme(Theme):
    @classmethod
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "clam")


class Win32Theme(Theme):
    @classmethod
    @windows_only
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "vista")


class AquaTheme(Theme):
    @classmethod
    @mac_only
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "aqua")


def native_theme() -> Theme:
    if System.os == "Windows":
        return Win32Theme
    elif System.os == "macOS":
        return AquaTheme
    return ClamTheme
