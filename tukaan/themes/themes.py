from __future__ import annotations

from abc import ABC, abstractclassmethod

from tukaan._info import System
from tukaan._tcl import Tcl
from tukaan._utils import linux_only, mac_only, windows_only
from tukaan.exceptions import TclError


class ThemeError(Exception):
    ...


class Theme(ABC):
    @abstractclassmethod
    def _use(cls):
        pass


class ClamTheme(Theme):
    @classmethod
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "clam")


class AquaTheme(Theme):
    @classmethod
    @mac_only
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "aqua")


class GtkTheme(Theme):
    __theme = None

    def __init__(self, theme: str | None = None) -> None:
        GtkTheme.__theme = theme

    @classmethod
    @linux_only
    def _use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "Gttk")
        if not cls.__theme:
            return

        try:
            Tcl.call(None, "ttk::theme::Gttk::setGtkTheme", cls.__theme)
        except TclError:
            raise ThemeError(f"invalid GTK theme name: {cls.__theme}")

    @classmethod
    @linux_only
    def get_themes(cls) -> list[str]:
        return sorted(Tcl.call([str], "ttk::theme::Gttk::availableGtkThemes"))

    @classmethod
    @linux_only
    def get_system_theme(cls) -> str:
        return Tcl.call(str, "ttk::theme::Gttk::currentThemeName")


class Win32Theme(Theme):
    @classmethod
    @windows_only
    def _use(cls):
        Tcl.call(None, "ttk::style", "theme", "use", "vista")


def native_theme(use_gtk: bool = True) -> Theme:
    if System.os == "Windows":
        return Win32Theme
    elif System.os == "macOS":
        return AquaTheme
    elif System.os == "Linux" and use_gtk:
        return GtkTheme
    return ClamTheme
