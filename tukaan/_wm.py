from __future__ import annotations

import ctypes
import re
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Final

from ._data import Size
from ._tcl import Tcl
from .colors import Color
from .enums import BackdropEffect, WindowState
from .exceptions import TclError

DWMWA_TRANSITIONS_FORCEDISABLED: Final[int] = 3
DWMWA_NONCLIENT_RTL_LAYOUT: Final[int] = 6
DWMWA_FORCE_ICONIC_REPRESENTATION: Final[int] = 7
DWMWA_USE_IMMERSIVE_DARK_MODE: Final[int] = 20
DWMWA_BORDER_COLOR: Final[int] = 34
DWMWA_CAPTION_COLOR: Final[int] = 35
DWMWA_TEXT_COLOR: Final[int] = 36

# https://github.com/minusium/MicaForEveryone/blob/master/MicaForEveryone.Win32/DesktopWindowManager.cs#L15
DWMWA_SYSTEMBACKDROP_TYPE: Final[int] = 38

# https://github.com/Brouilles/win32-mica/blob/main/main.cpp#L119
DWMWA_MICA_EFFECT: Final[int] = 1029


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


class WMProperties:
    def _get_title(self) -> str:
        return Tcl.call(str, "wm", "title", self._wm_path)

    def _set_title(self, new_title: str) -> None:
        Tcl.call(None, "wm", "title", self._wm_path, new_title)

    title = property(_get_title, _set_title)

    @Tcl.update_before
    def _get_x(self) -> int:
        return Tcl.call(int, "winfo", "x", self._wm_path)

    @Tcl.update_after
    def _set_x(self, new_x: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{new_x}+{self._get_y()}")

    x = property(_get_x, _set_x)

    @Tcl.update_before
    def _get_y(self) -> int:
        return Tcl.call(int, "winfo", "y", self._wm_path)

    @Tcl.update_after
    def _set_y(self, new_y: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{self._get_x()}+{new_y}")

    y = property(_get_y, _set_y)

    @Tcl.update_before
    def _get_width(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @Tcl.update_after
    def _set_width(self, new_width: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{new_width}x{self._get_height()}")

    width = property(_get_width, _set_width)

    @Tcl.update_before
    def _get_height(self) -> int:
        return Tcl.call(int, "winfo", "height", self._wm_path)

    @Tcl.update_after
    def _set_height(self, new_height: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{self._get_width()}x{new_height}")

    height = property(_get_height, _set_height)

    @Tcl.update_before
    def _get_size(self) -> Size:
        return Size(
            *map(
                int,
                re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[:2],
            )
        )

    @Tcl.update_after
    def _set_size(self, new_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_size, int):
            new_size = (new_size,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "{}x{}".format(*new_size))

    size = property(_get_size, _set_size)


class WindowManagerBase(ABC, WMProperties):
    _name: str
    _wm_path: str
    generate_event: Callable[[str], None]

    _current_state = WindowState.Normal

    def _generate_state_event(self):
        prev_state = self._current_state
        new_state = self.state

        if new_state == prev_state:
            return

        event = None
        un_event = None

        if new_state == "normal":
            event = "<<Restore>>"
        elif new_state == "maximized":
            event = "<<Maximize>>"
        elif new_state == "minimized":
            event = "<<Minimize>>"
        elif new_state == "hidden":
            event = "<<Hide>>"
        elif new_state == "fullscreen":
            event = "<<Fullscreen>>"

        if prev_state == "maximized":
            un_event = "<<Unmaximize>>"
        elif prev_state == "minimized":
            un_event = "<<Unminimize>>"
        elif prev_state == "hidden":
            un_event = "<<Unhide>>"
        elif prev_state == "fullscreen":
            un_event = "<<Unfullscreen>>"

        self.generate_event("<<StateChanged>>")

        if event:
            self.generate_event(event)

        if un_event:
            self.generate_event(un_event)

        self._current_state = new_state

    def minimize(self) -> None:
        Tcl.call(None, "wm", "iconify", self._wm_path)

    @abstractmethod
    def maximize(self) -> None:
        pass

    def fullscreen(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", True)

    def focus(self) -> None:
        Tcl.call(None, "focus", "-force", self._wm_path)

    def group(self, other: WindowManagerBase) -> None:
        Tcl.call(None, "wm", "group", self._wm_path, other._wm_path)

    def hide(self):
        Tcl.call(None, "wm", "withdraw", self._wm_path)

    def unhide(self):
        Tcl.call(None, "wm", "deiconify", self._wm_path)

    def on_close(self, func: Callable[[WindowManagerBase], None]) -> Callable[[], None]:
        def wrapper() -> None:
            if func(self):
                self.destroy()

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def id(self) -> int:
        return int(Tcl.call(str, "winfo", "id", self._wm_path), 16)

    @property
    def is_focused(self) -> bool:
        return Tcl.call(str, "focus", "-displayof") == self._wm_path

    @property
    def state(self):
        try:
            state = Tcl.call(str, "wm", "state", self._wm_path)
        except TclError as e:
            if not Tcl.call(bool, "winfo", "exists", self._wm_path):
                return WindowState.Closed
            raise e

        if state == "normal" and Tcl.windowing_system != "x11":  # needs further checking on X11
            return WindowState.Normal
        elif state == "iconic":
            return WindowState.Minimized
        elif state == "zoomed":
            return WindowState.Maximized
        elif state == "withdrawn":
            return WindowState.Hidden
        # fmt: off
        elif (
            Tcl.windowing_system == "x11" and
            Tcl.call(bool, "wm", "attributes", self._wm_path, "-zoomed")
        ):
            return WindowState.Maximized
        # fmt: on
        elif Tcl.call(bool, "wm", "attributes", self._wm_path, "-fullscreen"):
            return WindowState.FullScreen

        return WindowState.Normal

    ### Windows only stuff ###
    def set_backdrop_effect(self, *args, **kwargs) -> None:
        pass

    @property
    def is_toolwindow(self) -> None:
        pass

    @is_toolwindow.setter
    def is_toolwindow(self, *args) -> None:
        pass

    @property
    def border_color(self) -> None:
        pass

    @border_color.setter
    def border_color(self, *args) -> None:
        pass

    @property
    def immersive_dark_mode(self) -> None:
        pass

    @immersive_dark_mode.setter
    def immersive_dark_mode(self, *args) -> None:
        pass


class DWM(WindowManagerBase):
    """Windows"""

    def maximize(self) -> None:
        Tcl.call(None, "wm", "state", self._wm_path, "zoomed")

    @property
    def is_toolwindow(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._wm_path, "-toolwindow")

    @is_toolwindow.setter
    def is_toolwindow(self, value: bool) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", value)

    @property
    def border_color(self) -> Color:
        ...

    @border_color.setter
    def border_color(self, value: Color | str) -> None:
        if isinstance(value, Color):
            value = value.hex

        self._dwm_set_window_attribute(DWMWA_BORDER_COLOR, self._get_bgr_color(value))

    def set_backdrop_effect(
        self,
        effect: BackdropEffect = BackdropEffect.Blur,
        tint: Color | str | None = None,
        tint_opacity: float = 0.2,
    ) -> None:
        # Useful links:
        # https://github.com/Peticali/PythonBlurBehind/blob/main/blurWindow/blurWindow.py
        # https://github.com/sourcechord/FluentWPF/blob/master/FluentWPF/Utility/AcrylicHelper.cs

        build = sys.getwindowsversion().build
        has_mica = build >= 22000
        has_backdrop_type = build >= 22523

        if not has_mica and effect is BackdropEffect.Mica:
            # Mica is available only on Windows 11 build 22000+, fall back to acrylic
            effect = BackdropEffect.Acrylic

        if effect is BackdropEffect.No:
            gradient_color = 0

            # Remove `-transparentcolor`
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {{}}")

            self.unbind("<<Unmaximize>>")
        else:
            # Make an ABGR color from `tint` and `tint_opacity`
            # If `tint` is None, use the window background color
            bg_color = Tcl.eval(str, "ttk::style lookup . -background")

            if isinstance(tint, Color):
                tint_color = tint.hex
            else:
                if tint is None:
                    tint = Tcl.eval((int,), f"winfo rgb . {bg_color}")
                tint_color = Color(rgb=tuple(value >> 8 for value in tint)).hex

            tint_hex_a = str(hex(int(255 * tint_opacity)))[2:]
            tint_hex_bgr = self._get_bgr_color(tint_color)
            gradient_color = int(tint_hex_a + tint_hex_bgr, 16)

            # Make the window background, and each pixel with the same color
            # as the window background fully transparent.
            # These are the areas that will be blurred.
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {bg_color}")

            # When the window has `transparentcolor`, the whole window becomes unusable after unmaximizing.
            # Therefore we bind it to the <<Unmaximize>> event (see it below: WindowManager._generate_state_event),
            # so every time it changes state, it calls the _fullredraw method.
            # See DWM._fullredraw.__doc__ for more.
            self.bind("<<Unmaximize>>", self._fullredraw)

        accent_policy = AccentPolicy()
        accent_policy.AccentFlags = 2  # ACCENT_ENABLE_BLURBEHIND  <- try this with '4' bruhh :D
        accent_policy.AccentState = effect.value
        accent_policy.GradientColor = gradient_color

        wcad = WindowCompositionAttributeData()
        wcad.Attribute = 19  # WCA_ACCENT_POLICY
        wcad.Data = ctypes.cast(ctypes.pointer(accent_policy), ctypes.POINTER(ctypes.c_int))
        wcad.SizeOfData = ctypes.sizeof(accent_policy)

        self._set_window_composition_attribute(wcad)

        if effect is BackdropEffect.Mica:
            if has_backdrop_type:
                # https://github.com/minusium/MicaForEveryone/blob/master/MicaForEveryone.Win32/PInvoke/DWM_SYSTEMBACKDROP_TYPE.cs
                # Mica effect is 2
                self._dwm_set_window_attribute(DWMWA_SYSTEMBACKDROP_TYPE, 2)
            elif has_mica:
                self._dwm_set_window_attribute(DWMWA_MICA_EFFECT, 1)
        elif effect is BackdropEffect.No:
            # Remove Mica
            if has_backdrop_type:
                # None effect is 1
                self._dwm_set_window_attribute(DWMWA_SYSTEMBACKDROP_TYPE, 1)
            elif has_mica:
                self._dwm_set_window_attribute(DWMWA_MICA_EFFECT, 0)

    def _fullredraw(self) -> None:
        """
        Internal method

        Neither user32.RedrawWindow nor user32.UpdateWindow redraws the titlebar,
        so we need to explicitly minimize and then restore the window.
        To avoid visual effects, disable transitions on the window for that time.
        """

        self._dwm_set_window_attribute(DWMWA_TRANSITIONS_FORCEDISABLED, 1)
        self.minimize()
        self.restore()
        self._dwm_set_window_attribute(DWMWA_TRANSITIONS_FORCEDISABLED, 0)

    def _get_WHND(self):
        return int(Tcl.call(str, "wm", "frame", self._wm_path), 16)

    def _get_bgr_color(self, color: str) -> str:
        return color[5:7] + color[3:5] + color[1:3]

    def _dwm_set_window_attribute(self, rendering_policy: int, value: Any) -> None:
        value = ctypes.c_int(value)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            self._get_WHND(),
            rendering_policy,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

    def _set_window_composition_attribute(self, wcad: WindowCompositionAttributeData) -> None:
        ctypes.windll.user32.SetWindowCompositionAttribute(self._get_WHND(), wcad)


class Quartz(WindowManagerBase):
    """macOS"""

    def maximize(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", True)


class X11(WindowManagerBase):
    """GNU/Linux"""

    def maximize(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", True)


if sys.platform == "win32":
    WindowManager = DWM
elif sys.platform == "darwin":
    WindowManager = Quartz
else:
    WindowManager = X11
