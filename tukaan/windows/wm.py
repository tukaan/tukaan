from __future__ import annotations

import ctypes
import functools
import re
import sys
from enum import Enum
from fractions import Fraction
from typing import Callable, Sequence

from tukaan._images import Icon
from tukaan._misc import Position, Size
from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan.colors import Color
from tukaan.enums import Resizable, WindowBackdropType, WindowState, WindowType
from tukaan.exceptions import TukaanTclError

if sys.platform == "win32":
    windows_build = sys.getwindowsversion().build


class AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class WindowCompositionAttributeData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ctypes.c_int)),
        ("SizeOfData", ctypes.c_size_t),
    ]


class Margins(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


class DWMWA(Enum):
    TRANSITIONS_FORCEDISABLED = 3
    USE_IMMERSIVE_DARK_MODE = 20
    BORDER_COLOR = 34
    CAPTION_COLOR = 35
    TEXT_COLOR = 36
    SYSTEMBACKDROP_TYPE = 38  # Windows 11 build >= 22621
    MICA_EFFECT = 1029  # Undocumented, kinda buggy


class DesktopWindowManager:
    @staticmethod
    def set_window_attr(name_or_hwnd: str | int, attr: DWMWA, value: int) -> None:
        hwnd = (
            name_or_hwnd
            if isinstance(name_or_hwnd, int)
            else int(Tcl.call(str, "wm", "frame", name_or_hwnd), 16)
        )

        c_value = ctypes.c_int(value)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            attr.value,
            ctypes.byref(c_value),
            ctypes.sizeof(ctypes.c_int),
        )

    @classmethod
    def apply_backdrop_effect(cls, window_name: str, backdrop_type: int) -> None:
        hwnd = int(Tcl.call(str, "wm", "frame", window_name), 16)

        acp = AccentPolicy()
        acp.AccentFlags = 2  # ACCENT_ENABLE_BLURBEHIND
        acp.AccentState = 5
        acp.GradientColor = 0

        wcad = WindowCompositionAttributeData()
        wcad.Attribute = 19  # WCA_ACCENT_POLICY
        wcad.SizeOfData = ctypes.sizeof(acp)
        wcad.Data = ctypes.cast(ctypes.pointer(acp), ctypes.POINTER(ctypes.c_int))

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, wcad)

        if windows_build >= 22621:
            cls.set_window_attr(hwnd, DWMWA.SYSTEMBACKDROP_TYPE, backdrop_type)
        elif windows_build >= 22000:
            cls.set_window_attr(hwnd, DWMWA.MICA_EFFECT, 1 if backdrop_type else 0)


def _get_bgr_color(rgb_hex: str) -> int:
    return int(rgb_hex[5:7] + rgb_hex[3:5] + rgb_hex[1:3], 16)


class WindowManager:
    _current_state = "normal"
    _wm_path: str

    bind: Callable
    unbind: Callable

    def _get_state(self) -> str:
        try:
            state = Tcl.call(str, "wm", "state", self._wm_path)
        except TukaanTclError as e:
            # FIXME: what if the interpreter is destroyed?
            if not Tcl.call(bool, "winfo", "exists", self._wm_path):
                return "closed"
            raise e

        if state == "normal" and Tcl.windowing_system != "x11":  # needs further checking on X11
            return "normal"
        elif state == "iconic":
            return "minimized"
        elif state == "zoomed":
            return "maximized"
        elif state == "withdrawn":
            return "hidden"
        elif Tcl.windowing_system == "x11" and Tcl.call(
            bool, "wm", "attributes", self._wm_path, "-zoomed"
        ):
            return "maximized"
        elif Tcl.call(bool, "wm", "attributes", self._wm_path, "-fullscreen"):
            return "fullscreen"

        return "normal"

    def _gen_state_event(self):
        prev_state = self._current_state
        new_state = self._get_state()

        if new_state == prev_state or prev_state == "nostate":
            return

        events = ["<<StateChanged>>"]

        if new_state == "normal":
            events.append("<<Restore>>")
        elif new_state == "maximized":
            events.append("<<Maximize>>")
        elif new_state == "minimized":
            events.append("<<Minimize>>")
        elif new_state == "hidden":
            events.append("<<Hide>>")
        elif new_state == "fullscreen":
            events.append("<<Fullscreen>>")

        if prev_state == "maximized":
            events.extend(["<<Unmaximize>>", "<<__unmax_private__>>"])
        elif prev_state == "minimized":
            events.append("<<Unminimize>>")
        elif prev_state == "hidden":
            events.append("<<Unhide>>")
        elif prev_state == "fullscreen":
            events.append("<<Unfullscreen>>")

        for event in events:
            Tcl.call(None, "event", "generate", self, event)

        self._current_state = new_state

    def _force_redraw_titlebar(self) -> None:
        """
        Internal method, Windoze only

        Neither user32.RedrawWindow nor user32.UpdateWindow redraws the titlebar,
        so we need to explicitly iconify and then deiconify the window.
        To avoid visual effects, we disable the transitions on the window for that time.
        """
        hwnd = self.hwnd
        self._current_state = "nostate"

        DesktopWindowManager.set_window_attr(hwnd, DWMWA.TRANSITIONS_FORCEDISABLED, 1)
        Tcl.call(None, "wm", "iconify", self._wm_path)
        Tcl.call(None, "wm", "deiconify", self._wm_path)
        DesktopWindowManager.set_window_attr(hwnd, DWMWA.TRANSITIONS_FORCEDISABLED, 0)

        self._current_state = self._get_state()

    def minimize(self) -> None:
        Tcl.call(None, "wm", "iconify", self._wm_path)

    def maximize(self) -> None:
        if Tcl.windowing_system == "x11":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", True)
        else:
            Tcl.call(None, "wm", "state", self._wm_path, "zoomed")

    def restore(self) -> None:
        state = self._get_state()

        if state in {"hidden", "minimized"}:
            Tcl.call(None, "wm", "deiconify", self._wm_path)
        elif state == "maximized":
            if Tcl.windowing_system == "x11":
                Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", False)
            else:
                Tcl.call(None, "wm", "state", self._wm_path, "normal")
        elif state == "fullscreen":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", False)

    def fullscreen(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", True)

    def focus(self) -> None:
        Tcl.call(None, "focus", "-force", self._wm_path)

    def group(self, other: WindowManager) -> None:
        Tcl.call(None, "wm", "group", self._wm_path, other._wm_path)

    def hide(self) -> None:
        Tcl.call(None, "wm", "withdraw", self._wm_path)

    def unhide(self) -> None:
        Tcl.call(None, "wm", "deiconify", self._wm_path)

    def on_close(self, func: Callable[[WindowManager], None]) -> Callable[[], None]:
        @functools.wraps(func)
        def wrapper() -> None:
            if func(self):
                self.destroy()

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def focused(self) -> int:
        return Tcl.call(str, "focus", "-displayof", self._wm_path)

    @property
    @Tcl.redraw_before
    def visible(self) -> bool:
        return Tcl.call(bool, "winfo", "ismapped", self._wm_path)

    @property
    def id(self) -> int:
        return int(Tcl.call(str, "winfo", "id", self._wm_path), 16)

    @property
    def hwnd(self) -> int:
        return int(Tcl.call(str, "wm", "frame", self._wm_path), 16)

    @property
    def state(self) -> WindowState:
        WindowState(self._get_state())

    @property
    @Tcl.redraw_before
    def x(self) -> int:
        return Tcl.call(int, "winfo", "x", self._wm_path)

    @x.setter
    @Tcl.with_redraw
    def x(self, value: int) -> None:
        y = Tcl.call(int, "winfo", "y", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{value}+{y}")

    @property
    @Tcl.redraw_before
    def y(self) -> int:
        return Tcl.call(int, "winfo", "y", self._wm_path)

    @y.setter
    @Tcl.with_redraw
    def y(self, value: int) -> None:
        x = Tcl.call(int, "winfo", "x", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{x}+{value}")

    @property
    @Tcl.redraw_before
    def width(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @width.setter
    @Tcl.with_redraw
    def width(self, value: int) -> None:
        height = Tcl.call(int, "winfo", "height", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{value}x{height}")

    @property
    @Tcl.redraw_before
    def height(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @height.setter
    @Tcl.with_redraw
    def height(self, value: int) -> None:
        width = Tcl.call(int, "winfo", "width", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{width}x{value}")

    @property
    @Tcl.redraw_before
    def position(self) -> Position:
        return Position(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[2:])
        )

    @position.setter
    @Tcl.redraw_after
    def position(self, value: Position | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "+{}+{}".format(*value))

    @property
    @Tcl.redraw_before
    def size(self) -> Size:
        return Size(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[:2])
        )

    @size.setter
    @Tcl.redraw_after
    def size(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "{}x{}".format(*value))

    @property
    @Tcl.redraw_before
    def min_size(self) -> Size:
        return Size(*Tcl.call([int], "wm", "minsize", self._wm_path))

    @min_size.setter
    @Tcl.redraw_after
    def min_size(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "minsize", self._wm_path, *value)

    @property
    @Tcl.redraw_before
    def max_size(self) -> Size:
        return Size(*Tcl.call([int], "wm", "maxsize", self._wm_path))

    @max_size.setter
    @Tcl.redraw_after
    def max_size(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "maxsize", self._wm_path, *value)

    @property
    def title(self) -> str:
        return Tcl.call(str, "wm", "title", self._wm_path)

    @title.setter
    def title(self, value: str) -> None:
        Tcl.call(None, "wm", "title", self._wm_path, value)

    @property
    def always_on_top(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._wm_path, "-topmost")

    @always_on_top.setter
    def always_on_top(self, value: bool = False) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-topmost", value)

    @property
    def opacity(self) -> float:
        return Tcl.call(float, "wm", "attributes", self._wm_path, "-alpha")

    @opacity.setter
    def opacity(self, value: float) -> None:
        if Tcl.windowing_system == "x11":
            Tcl.call(None, "tkwait", "visibility", self._wm_path)

        Tcl.call(None, "wm", "attributes", self._wm_path, "-alpha", value)

    @property
    def size_increment(self) -> Size:
        return Size(*Tcl.call([str], "wm", "grid", self._wm_path)[2:])

    @size_increment.setter
    def size_increment(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "grid", self._wm_path, 1, 1, *value)

    @property
    @Tcl.redraw_before
    def aspect_ratio(self) -> None | tuple[Fraction, Fraction]:
        result = Tcl.call((int,), "wm", "aspect", self._wm_path)
        if not result:
            return None
        return Fraction(*result[:2]), Fraction(*result[2:])

    @aspect_ratio.setter
    @Tcl.redraw_after
    def aspect_ratio(
        self,
        value: tuple[float, float] | tuple[Fraction, Fraction] | float | None,
    ) -> None:
        if value is None:
            Tcl.call(None, "wm", "aspect", self._wm_path, *("",) * 4)
            return

        if isinstance(value, (int, float)):
            min_ = max_ = value
        else:
            min_, max_ = value

        if not isinstance(min_, Fraction):
            min_ = Fraction.from_float(min_).limit_denominator()

        if not isinstance(max_, Fraction):
            max_ = Fraction.from_float(max_).limit_denominator()

        Tcl.call(
            None, "wm", "aspect", self._wm_path, *min_.as_integer_ratio(), *max_.as_integer_ratio()
        )

    @property
    def resizable(self) -> Resizable:
        return Resizable(Tcl.call((str, str), "wm", "resizable", self._wm_path))

    @resizable.setter
    def resizable(self, value: Resizable) -> None:
        Tcl.call(None, "wm", "resizable", self._wm_path, *value.value)

    @property
    def type(self) -> WindowType:
        if Tcl.windowing_system == "win32":
            if Tcl.call(bool, "wm", "attributes", self._wm_path, "-toolwindow"):
                return WindowType.Utility
            return WindowType.Normal
        elif Tcl.windowing_system == "x11":
            return Tcl.call(WindowType, "wm", "attributes", self._wm_path, "-type")
        return WindowType.Normal

    @type.setter
    def type(self, value: WindowType) -> None:
        if Tcl.windowing_system == "win32":
            if value is WindowType.ToolWindow:
                Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", True)
            elif value is WindowType.Normal:
                Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", False)
        elif Tcl.windowing_system == "x11":
            Tcl.call(None, "wm", "attributes", self._wm_path, value)

    @property
    def icon(self) -> Icon:
        return Tcl.call(Icon, "wm", "iconphoto", self._wm_path)

    @icon.setter
    def icon(self, image: Icon) -> None:
        Tcl.call(None, "wm", "iconphoto", self._wm_path, image)

    @property
    @Platform.windows_only
    def border_color(self) -> None:
        ...

    @border_color.setter
    @Platform.windows_only
    def border_color(self, value: Color | str) -> None:
        if windows_build < 22000:
            return None

        DesktopWindowManager.set_window_attr(
            self._wm_path, DWMWA.BORDER_COLOR, _get_bgr_color(value)
        )

    @property
    @Platform.windows_only
    def titlebar_color(self) -> None:
        ...

    @titlebar_color.setter
    @Platform.windows_only
    def titlebar_color(self, value: Color | str) -> None:
        if windows_build < 22000:
            return None

        DesktopWindowManager.set_window_attr(
            self._wm_path, DWMWA.CAPTION_COLOR, _get_bgr_color(value)
        )

    @property
    @Platform.windows_only
    def titlebar_text_color(self) -> None:
        ...

    @titlebar_text_color.setter
    @Platform.windows_only
    def titlebar_text_color(self, value: Color | str) -> None:
        if windows_build < 22000:
            return None

        DesktopWindowManager.set_window_attr(self._wm_path, DWMWA.TEXT_COLOR, _get_bgr_color(value))

    @property
    @Platform.windows_only
    def use_dark_mode_decorations(self) -> None:
        ...

    @use_dark_mode_decorations.setter
    @Platform.windows_only
    def use_dark_mode_decorations(self, value: bool) -> None:
        if windows_build < 22000:
            return None

        DesktopWindowManager.set_window_attr(
            self._wm_path, DWMWA.USE_IMMERSIVE_DARK_MODE, int(value)
        )

    @Platform.windows_only
    @Tcl.with_redraw
    def set_backdrop_effect(
        self,
        backdrop_type: WindowBackdropType | None = WindowBackdropType.Mica,
        dark: bool = False,
    ) -> None:
        if windows_build < 22000:
            return

        if backdrop_type is None:
            backdrop_type = WindowBackdropType.Normal

        if backdrop_type is WindowBackdropType.Normal:
            Tcl.call(None, "wm", "attributes", self._wm_path, "-transparentcolor", "")
            Tcl.call(None, "bind", self._wm_path, "<<__unmax_private__>>", "")
        else:
            # Make the window background, and each pixel with the
            # same color as the window background fully transparent.
            # These are the areas where the backdrop effect will be applied.
            bg_color = Tcl.eval(str, "ttk::style lookup . -background")
            Tcl.call(None, "wm", "attributes", self._wm_path, "-transparentcolor", bg_color)

            # When the window has `transparentcolor`, the whole window
            # becomes unusable after unmaximizing. Therefore we bind it to the
            # <<__unmax_private__>> event (<<Unmaximize>>, but it's private, so the user can't unbind it)
            # so every time it changes state, it calls the _force_redraw_titlebar method.
            # See self._force_redraw_titlebar.__doc__ for more.
            Tcl.call(
                None,
                "bind",
                self._wm_path,
                "<<__unmax_private__>>",
                self._force_redraw_titlebar,
            )

        DesktopWindowManager.apply_backdrop_effect(self._wm_path, backdrop_type.value)

        self.use_dark_mode_decorations = dark
        self._force_redraw_titlebar()
