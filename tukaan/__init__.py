import sys

__author__ = "rdbende"
__license__ = "MIT"
__version__ = "0.2.0"

from ._events import KeySeq
from ._images import Icon, IconFactory, Image
from ._system import Platform
from ._variables import BoolVar, FloatVar, IntVar, StringVar
from .a11y.a11y import Accessibility
from .app import App
from .clipboard import Clipboard
from .colors import Color, cmyk, hsl, hsv, rgb
from .fonts.font import Font, font
from .fonts.fontfile import FontFile, OpenTypeFont, TrueTypeCollection, TrueTypeFont
from .screen import Screen, ScreenDistance, cm, inch, mm
from .theming import AquaTheme, ClamTheme, KolorScheme, LookAndFeel, NativeTheme, Theme, Win32Theme
from .time import Time
from .timeouts import Timeout, Timer
from .widgets.button import Button
from .widgets.checkbox import CheckBox
from .widgets.combobox import ComboBox
from .widgets.frame import Frame
from .widgets.label import Label
from .widgets.progressbar import ProgressBar
from .widgets.radiobutton import RadioButton, RadioGroup
from .widgets.scrollbar import ScrollBar
from .widgets.separator import Separator
from .widgets.slider import Slider
from .widgets.spinbox import SpinBox
from .widgets.splitview import SplitView
from .widgets.tabview import TabView
from .widgets.textbox import TextBox
from .windows.main_window import MainWindow
from .windows.window import Window

__all__: list = []  # Making star imports impossible. Is it illegal?


class _RequiredVersion:
    def __splitver(self, version_str):
        return tuple(map(int, version_str.split(".")))

    def __eq__(self, version):
        if version != __version__:
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version}.\n"
                + f"Use 'pip install tukaan=={version}' to install the required version of Tukaan."
            )

    def __le__(self, version):
        if self.__splitver(__version__) > self.__splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or older.\n"
                + f"Use 'pip install tukaan=={version}' to install an older version of Tukaan."
            )

    def __ge__(self, version):
        if self.__splitver(__version__) < self.__splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or newer.\n"
                + "Use 'pip install --upgrade tukaan' to install the newest version of Tukaan."
            )


required_version = _RequiredVersion()
