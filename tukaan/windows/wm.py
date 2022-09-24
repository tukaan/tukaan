from __future__ import annotations

import ctypes
import functools
import re
import sys
from fractions import Fraction
from typing import Callable, Sequence

from tukaan._data import Position, Size
from tukaan._images import Icon
from tukaan._tcl import Tcl
from tukaan._utils import windows_only
from tukaan.colors import Color, rgb
from tukaan.enums import Resizable, WindowBackdropEffect, WindowState, WindowType
from tukaan.exceptions import TukaanTclError


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


class DWM:
    DWMWA_TRANSITIONS_FORCEDISABLED = 3
    DWMWA_NONCLIENT_RTL_LAYOUT = 6
    DWMWA_FORCE_ICONIC_REPRESENTATION = 7
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36

    # https://github.com/minusium/MicaForEveryone/blob/master/MicaForEveryone.Win32/DesktopWindowManager.cs#L15
    DWMWA_SYSTEMBACKDROP_TYPE = 38

    # https://github.com/Brouilles/win32-mica/blob/main/main.cpp#L119
    DWMWA_MICA_EFFECT = 1029

    @staticmethod
    def _create_abgr(rgb_hex: str, opacity: float) -> int:
        alpha = hex(int(opacity * 255))
        abgr_hex = alpha[2:] + rgb_hex[5:7] + rgb_hex[3:5] + rgb_hex[1:3]

        return int(abgr_hex, 16)

    @staticmethod
    def _get_accent_policy_wcad(backdrop_type: int, tint: int) -> WindowCompositionAttributeData:
        accent_policy = AccentPolicy()
        accent_policy.AccentFlags = 2  # ACCENT_ENABLE_BLURBEHIND <- try this with 4 bruhh :D
        accent_policy.AccentState = backdrop_type
        accent_policy.GradientColor = tint

        wcad = WindowCompositionAttributeData()
        wcad.Attribute = 19  # WCA_ACCENT_POLICY
        wcad.Data = ctypes.cast(ctypes.pointer(accent_policy), ctypes.POINTER(ctypes.c_int))
        wcad.SizeOfData = ctypes.sizeof(accent_policy)

        return wcad

    @classmethod
    def _set_window_attr(cls, hwnd: int, rendering_policy: int, value: int) -> None:
        c_value = ctypes.c_int(value)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, rendering_policy, ctypes.byref(c_value), ctypes.sizeof(c_value)
        )

    @classmethod
    def _set_wca(cls, hwnd: int, wcad: WindowCompositionAttributeData) -> None:
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, wcad)

    @classmethod
    def apply_backdrop_effect(
        cls,
        hwnd: int,
        backdrop_type: int,
        tint: str,
        tint_opacity: float,
    ) -> None:
        windows_build = sys.getwindowsversion().build  # type: ignore

        if windows_build < 22000 and backdrop_type == 5:
            # Mica is available only on Windows 11 build 22000+, fall back to acrylic
            backdrop_type = 4

        cls._set_wca(
            hwnd, cls._get_accent_policy_wcad(backdrop_type, cls._create_abgr(tint, tint_opacity))
        )

        if backdrop_type == 5:
            if windows_build >= 22523:
                cls._set_window_attr(hwnd, cls.DWMWA_SYSTEMBACKDROP_TYPE, 2)
            else:
                # Use the undocumented DWMWA_MICA_EFFECT option
                cls._set_window_attr(hwnd, cls.DWMWA_MICA_EFFECT, 1)

    @classmethod
    def remove_backdrop_effect(cls, hwnd: int) -> None:
        windows_build = sys.getwindowsversion().build  # type: ignore

        cls._set_wca(hwnd, cls._get_accent_policy_wcad(0, 0))

        if windows_build >= 22523:
            cls._set_window_attr(hwnd, cls.DWMWA_SYSTEMBACKDROP_TYPE, 1)
        elif windows_build >= 22000:
            cls._set_window_attr(hwnd, cls.DWMWA_MICA_EFFECT, 0)


class WindowManager:
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

    def _windows_redraw_titlebar(self) -> None:
        """
        Internal method, Windoze only

        Neither user32.RedrawWindow nor user32.UpdateWindow redraws the titlebar,
        so we need to explicitly iconify and then deiconify the window.
        To avoid visual effects, disable transitions on the window for that time.
        """
        hwnd = self.hwnd

        DWM._set_window_attr(hwnd, DWM.DWMWA_TRANSITIONS_FORCEDISABLED, 1)
        Tcl.call(None, "wm", "iconify", self._wm_path)
        Tcl.call(None, "wm", "deiconify", self._wm_path)
        DWM._set_window_attr(hwnd, DWM.DWMWA_TRANSITIONS_FORCEDISABLED, 0)

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
    @Tcl.update_before
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
    @Tcl.update_before
    def x(self) -> int:
        return Tcl.call(int, "winfo", "x", self._wm_path)

    @x.setter
    @Tcl.updated
    def x(self, value: int) -> None:
        y = Tcl.call(int, "winfo", "y", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{value}+{y}")

    @property
    @Tcl.update_before
    def y(self) -> int:
        return Tcl.call(int, "winfo", "y", self._wm_path)

    @y.setter
    @Tcl.updated
    def y(self, value: int) -> None:
        x = Tcl.call(int, "winfo", "x", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{x}+{value}")

    @property
    @Tcl.update_before
    def width(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @width.setter
    @Tcl.updated
    def width(self, value: int) -> None:
        height = Tcl.call(int, "winfo", "height", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{value}x{height}")

    @property
    @Tcl.update_before
    def height(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @height.setter
    @Tcl.updated
    def height(self, value: int) -> None:
        width = Tcl.call(int, "winfo", "width", self._wm_path)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{width}x{value}")

    @property
    @Tcl.update_before
    def position(self) -> Position:
        return Position(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[2:])
        )

    @position.setter
    @Tcl.update_after
    def position(self, value: Position | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "+{}+{}".format(*value))

    @property
    @Tcl.update_before
    def size(self) -> Size:
        return Size(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[:2])
        )

    @size.setter
    @Tcl.update_after
    def size(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "{}x{}".format(*value))

    @property
    @Tcl.update_before
    def min_size(self) -> Size:
        return Size(*Tcl.call([int], "wm", "minsize", self._wm_path))

    @min_size.setter
    @Tcl.update_after
    def min_size(self, value: Size | Sequence[int] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "minsize", self._wm_path, *value)

    @property
    @Tcl.update_before
    def max_size(self) -> Size:
        return Size(*Tcl.call([int], "wm", "maxsize", self._wm_path))

    @max_size.setter
    @Tcl.update_after
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
    @Tcl.update_before
    def aspect_ratio(self) -> None | tuple[Fraction, Fraction]:
        result = Tcl.call((int,), "wm", "aspect", self._wm_path)
        if not result:
            return None
        return Fraction(*result[:2]), Fraction(*result[2:])

    @aspect_ratio.setter
    @Tcl.update_after
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
            min_ = Fraction.from_float(min_)

        if not isinstance(max_, Fraction):
            max_ = Fraction.from_float(max_)

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

    #@windows_only
    def set_backdrop_effect(
        self,
        backdrop_type: WindowBackdropEffect | None = WindowBackdropEffect.Mica,
        tint: Color | str | None = None,
        tint_opacity: float = 0.2,
    ) -> None:
        if backdrop_type is None or backdrop_type is WindowBackdropEffect.Normal:
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {{}}")
            self.unbind("<<__unmax_private__>>")
            DWM.remove_backdrop_effect(self.hwnd)
        else:
            bg_color = Tcl.eval(str, "ttk::style lookup . -background")

            if isinstance(tint, Color):
                color = tint.hex
            elif tint is None:
                tint_16_bit = Tcl.eval((int,), f"winfo rgb . {bg_color}")
                color = rgb(*(value >> 8 for value in tint_16_bit))

            # Make the window background, and each pixel with the same color
            # as the window background fully transparent.
            # These are the areas that will be blurred.
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {bg_color}")

            # When the window has `transparentcolor`, the whole window becomes unusable after unmaximizing.
            # Therefore we bind it to the <<__unmax_private__>> event, so every time it changes state,
            # it calls the _windows_redraw_titlebar method.
            # See _windows_redraw_titlebar.__doc__ for more.
            self.bind("<<__unmax_private__>>", self._windows_redraw_titlebar)

            DWM.apply_backdrop_effect(self.hwnd, backdrop_type.value, color, tint_opacity)

        self._windows_redraw_titlebar()
