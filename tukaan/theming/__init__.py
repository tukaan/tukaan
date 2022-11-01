import shutil
from pathlib import Path

from tukaan._system import Platform
from tukaan._tcl import Tcl

from .kolorscheme import KolorScheme
from .lookandfeel import LookAndFeel
from .themes import AquaTheme, Theme, Win32Theme


class ClamTheme(Theme):
    is_native = False

    @classmethod
    def use(cls) -> None:
        if not cls._inited and not KolorScheme._inited:
            Tcl.call(None, "source", Path(__file__).parent / "clam.tcl")
            cls._inited = True

        Tcl.call(None, "ttk::style", "theme", "use", "clam")
        Tcl.call(None, "::ttk::theme::clam::configure_colors")


if Platform.os == "Windows":
    NativeTheme = Win32Theme
elif Platform.os == "macOS":
    NativeTheme = AquaTheme
elif shutil.which("kreadconfig5"):
    NativeTheme = KolorScheme
    LookAndFeel._kreadconfig_available = True
else:
    NativeTheme = ClamTheme
