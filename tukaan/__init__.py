__all__: list = []  # Making star imports impossible. Is it illegal?
__author__ = "rdbende"
__license__ = "MIT license"
__package__ = "tukaan"
__version__ = "0.0.1.dev0"


import sys

from ._enums import (
    Alignment,
    BackdropEffect,
    CaretStyle,
    ImagePosition,
    InactiveCaretStyle,
    Justify,
    Resizable,
    Wrap,
)
from ._events import DragObject, KeySeq
from ._images import Icon, IconFactory, Image
from ._info import Clipboard, Machine, Pointer, Screen, System
from ._variables import Boolean, Float, Integer, String
from .colors import cmyk, hsl, hsv, rgb
from .fonts import Font, font
from .screen_distance import ScreenDistance, cm, inch, mm
from .time import TimeConstructor as Time
from .timeouts import Timeout, Timer
from .widgets.button import Button
from .widgets.checkbox import CheckBox
from .widgets.combobox import ComboBox
from .widgets.entry import Entry
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
from .widgets.textbox import TabStop, TextBox
from .window import App, Window, _ConfigObject

Config = _ConfigObject()


class _RequiredVersion:
    def splitver(self, version_str):
        return tuple(map(int, version_str.split(".")))

    def __eq__(self, version):
        if version != __version__:
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version}.\n"
                f"Use 'pip install tukaan=={version}' to install the required version of Tukaan."
            )

    def __le__(self, version):
        if self.splitver(__version__) > self.splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or older.\n"
                f"Use 'pip install tukaan=={version}' to install an older version of Tukaan."
            )

    def __ge__(self, version):
        if self.splitver(__version__) < self.splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(
                f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or newer.\n"
                "Use 'pip install --upgrade tukaan' to install the newest version of Tukaan."
            )


required_version = _RequiredVersion()
