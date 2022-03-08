__all__: list = []  # Making wildcard imports impossible. Is it illegal?
__author__ = "rdbende"
__package__ = "tukaan"
__version__ = "0.0.0"
import sys

from ._events_n_bindings import DragObject, KeySeq
from ._font import Font
from ._images import Icon, IconFactory, Image
from ._info import Machine, Memory, Screen, System
from ._misc import Clipboard, Color, Cursor
from ._units import MemoryUnit, ScreenDistance
from ._variables import Boolean, Float, Integer, String
from .button import Button
from .checkbox import CheckBox
from .entry import Entry
from .frame import Frame
from .label import Label
from .progressbar import ProgressBar
from .radiobutton import RadioButton, RadioGroup
from .scrollbar import Scrollbar
from .separator import Separator
from .slider import Slider
from .tabview import TabView
from .textbox import TextBox
from .timeout import Timer
from .window import App, Window


class _RequiredVersion:
    def splitver(self, version_str):
        return tuple(map(int, version_str.split(".")))
    
    def __eq__(self, version):
        if version != __version__:
            sys.tracebacklimit = 0
            raise RuntimeError(f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version}.\n"
                                f"Use 'pip install tukaan=={version}' to install the required version of Tukaan.")

    def __le__(self, version):
        if self.splitver(__version__) > self.splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or older.\n"
                                f"Use 'pip install tukaan=={version}' to install an older version of Tukaan.")

    def __ge__(self, version):
        if self.splitver(__version__) < self.splitver(version):
            sys.tracebacklimit = 0
            raise RuntimeError(f"you have Tukaan version {__version__} installed, which is incompatible with your code that requires Tukaan {version} or newer.\n"
                                "Use 'pip install --upgrade tukaan' to install the newest version of Tukaan.")

# required_version = _RequiredVersion()  # uncomment when release to Pypi
