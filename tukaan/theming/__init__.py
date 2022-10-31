import shutil

from tukaan._system import Platform

from .kolorscheme import KolorScheme
from .lookandfeel import LookAndFeel
from .themes import AquaTheme, ClamTheme, Theme, Win32Theme

if Platform.os == "Windows":
    NativeTheme = Win32Theme
elif Platform.os == "macOS":
    NativeTheme = AquaTheme
elif shutil.which("kreadconfig5"):
    NativeTheme = KolorScheme
    LookAndFeel._kreadconfig_available = True
else:
    NativeTheme = ClamTheme
