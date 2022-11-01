from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tukaan._system import Platform
from tukaan._tcl import Tcl

from .lookandfeel import LookAndFeel


class Theme(ABC):
    is_native: bool
    _inited: bool = False

    @classmethod
    @abstractmethod
    def use(cls) -> None:
        pass


class Win32Theme(Theme):
    is_native = True

    @classmethod
    @Platform.windows_only
    def use(cls) -> None:
        if not cls._inited:
            Tcl.call(None, "source", Path(__file__).parent / "win32.tcl")
            cls._inited = True

        Tcl.call(None, "ttk::style", "theme", "use", "vista")
        Tcl.call(None, "::ttk::theme::vista::configure_colors")


class AquaTheme(Theme):
    is_native = True

    @classmethod
    @Platform.mac_only
    def use(cls) -> None:
        if not cls._inited:
            Tcl.call(None, "source", Path(__file__).parent / "aqua.tcl")
            cls._inited = True

        Tcl.call(None, "ttk::style", "theme", "use", "aqua")
        Tcl.call(None, "::ttk::theme::aqua::configure_colors")
