from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tukaan._system import Platform
from tukaan._tcl import Tcl

from .lookandfeel import LookAndFeel


class Theme(ABC):
    is_native: bool

    @classmethod
    @abstractmethod
    def use(cls) -> None:
        pass


class ClamTheme(Theme):
    is_native = False

    @classmethod
    def use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "clam")


class Win32Theme(Theme):
    is_native = True

    @classmethod
    @Platform.windows_only
    def use(cls) -> None:
        Tcl.call(None, "ttk::style", "theme", "use", "vista")


class AquaTheme(Theme):
    is_native = True

    @classmethod
    @Platform.mac_only
    def use(cls) -> None:
        Tcl.eval(None, (Path(__file__).parent / "aqua.tcl").read_text())
        Tcl.call(None, "ttk::style", "theme", "use", "aqua")
        Tcl.call(None, "::ttk::theme::aqua::configure_colors")
