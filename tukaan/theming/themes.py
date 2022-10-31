from __future__ import annotations

from abc import ABC, abstractmethod

from tukaan._system import Platform
from tukaan._tcl import Tcl

from .lookandfeel import LookAndFeel


class Theme(ABC):
    @classmethod
    @abstractmethod
    def use(cls) -> None:
        pass


class ClamTheme(Theme):
    @classmethod
    def use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "clam")
        LookAndFeel._is_current_theme_native = False


class Win32Theme(Theme):
    @classmethod
    @Platform.windows_only
    def use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "vista")
        LookAndFeel._is_current_theme_native = True


class AquaTheme(Theme):
    @classmethod
    @Platform.mac_only
    def use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "aqua")
        LookAndFeel._is_current_theme_native = True
