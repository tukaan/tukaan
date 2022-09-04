def troubleshooting():
    import sys

    if sys.version_info < (3, 7):
        raise RuntimeError(
            f"Your Python version is too old ({'.'.join(map(str, sys.version_info[:3]))}). "
            + "Please install Python 3.7 or newer in order to use Tukaan."
        ) from None

    try:
        import _tkinter
    except ModuleNotFoundError as e:
        if sys.platform == "win32":
            msg = """Please modify your Python installation and make sure \
that the "tcl/tk and IDLE" option is turned on in the Optional features page."""
        else:
            msg = "Please install the `python3-tk` package with your package manager."

        raise RuntimeError(
            f"Tcl/Tk for Python is not installed on your system.\n{' ' * 14}{msg}"
        ) from None
    else:
        if float(_tkinter.TK_VERSION) < 8.6:
            if sys.platform == "win32":
                msg = """Please upgrade your Python installation, and make sure \
that the "tcl/tk and IDLE" option is turned on in the Optional features page."""
            else:
                msg = "Please reinstall the `python3-tk` package with your package manager."

            raise RuntimeError(
                f"Your Tcl/Tk version is too old ({_tkinter.TK_VERSION}). {msg}"
            ) from None

    try:
        from PIL import ImageTk
    except ImportError:
        raise RuntimeError(
            "Tk support for Pillow is not installed on your system. "
            + "Please install the `python3-pil.imagetk` package your package manager."
        ) from None


troubleshooting()

import sys

from .__version__ import __author__, __license__, __version__
from ._events import DragObject, KeySeq
from ._images import Icon, IconFactory, Image
from ._info import Clipboard, Pointer, Screen, System
from ._variables import Boolean, Float, Integer, String
from .app import App
from .colors import Color, cmyk, hsl, hsv, rgb
from .fonts.font import Font, font
from .fonts.fontfile import FontFile, OpenTypeFont, TrueTypeCollection, TrueTypeFont
from .screen_distance import ScreenDistance, cm, inch, mm
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
from .widgets.window import Window

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
