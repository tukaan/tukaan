from __future__ import annotations

from abc import ABC, abstractclassmethod

from tukaan._behaviour import classproperty, instanceclassmethod
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
    _theme = None

    def __init__(self, theme: str | None = None) -> None:
        self._theme = theme

    @instanceclassmethod
    @linux_only
    def _use(self_or_cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "Gttk")
        if self_or_cls._theme:
            try:
                Tcl.call(None, "ttk::theme::Gttk::setGtkTheme", self_or_cls._theme)
            except TclError:
                raise ThemeError(f"invalid GTK theme name: {self_or_cls._theme}")

    @classproperty
    @linux_only
    def themes(cls) -> list[str]:
        return sorted(Tcl.call([str], "ttk::theme::Gttk::availableGtkThemes"))

    @classproperty
    @linux_only
    def system_theme(cls) -> str:
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
