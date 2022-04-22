from __future__ import annotations

import ctypes
import platform
import re
import sys
import warnings
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from tukaan.themes import AquaTheme, ClamTheme, Theme, Win32Theme, native_theme

from ._enums import BackdropEffect, Resizable
from ._images import PIL_TclConverter
from ._layouts import ContainerLayoutManager
from ._structures import Position, Size
from ._tcl import Tcl
from ._utils import _commands, windows_only
from .colors import Color
from .exceptions import TclError
from .Serif import load_serif
from .widgets._base import BaseWidget, TkWidget


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


DWMWA_TRANSITIONS_FORCEDISABLED = 3
DWMWA_NONCLIENT_RTL_LAYOUT = 6
DWMWA_FORCE_ICONIC_REPRESENTATION = 7
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWA_SYSTEMBACKDROP_TYPE = 38  # https://github.com/minusium/MicaForEveryone/blob/master/MicaForEveryone.Win32/DesktopWindowManager.cs#L15
DWMWA_MICA_EFFECT = 1029  # https://github.com/Brouilles/win32-mica/blob/main/main.cpp#L119


class Titlebar:
    _wm_path: str

    _is_immersive_dark_mode_used = False
    _is_preview_disabled = False
    _is_rtl_titlebar_used = False
    _bg_color = None
    _fg_color = None

    def __init__(self, window):
        self._window = window

    def get_dark_mode(self) -> bool:
        return self._is_immersive_dark_mode_used

    @windows_only
    def set_dark_mode(self, is_used: bool = False) -> None:
        if sys.getwindowsversion().build >= 19041:
            self._window._dwm_set_window_attribute(DWMWA_USE_IMMERSIVE_DARK_MODE, int(is_used))

            # Need to redraw the titlebar
            self._window._dwm_set_window_attribute(DWMWA_TRANSITIONS_FORCEDISABLED, 1)
            self._window.minimize()
            self._window.restore()
            self._window._dwm_set_window_attribute(DWMWA_TRANSITIONS_FORCEDISABLED, 0)

        self._is_immersive_dark_mode_used = is_used

    dark_mode = property(get_dark_mode, set_dark_mode)

    def get_rtl_layout(self) -> bool:
        return self._is_rtl_titlebar_used

    @windows_only
    def set_rtl_layout(self, is_used: bool = False) -> None:
        self._window._dwm_set_window_attribute(DWMWA_NONCLIENT_RTL_LAYOUT, int(is_used))
        self._is_rtl_titlebar_used = is_used

    rtl_layout = property(get_rtl_layout, set_rtl_layout)

    def get_bg_color(self) -> Color | None:
        if self._bg_color is not None:
            return Color(self._bg_color)
        return None

    @windows_only
    def set_bg_color(self, color: Color) -> None:
        self._bg_color = color = color.hex
        int_color = int(color[5:7] + color[3:5] + color[1:3], 16)
        self._window._dwm_set_window_attribute(DWMWA_CAPTION_COLOR, int_color)

    bg_color = property(get_bg_color, set_bg_color)

    def get_fg_color(self) -> Color | None:
        if self._fg_color is not None:
            return Color(self._fg_color)
        return None

    @windows_only
    def set_fg_color(self, color: Color) -> None:
        self._fg_color = color = color.hex
        int_color = int(color[5:7] + color[3:5] + color[1:3], 16)
        self._window._dwm_set_window_attribute(DWMWA_TEXT_COLOR, int_color)

    fg_color = property(get_fg_color, set_fg_color)


class DesktopWindowManager:
    _border_color = None
    bind: Callable
    minimize: Callable
    restore: Callable
    unbind: Callable
    _wm_frame: int
    _wm_path: str

    def _dwm_set_window_attribute(self, rendering_policy: int, value: Any) -> None:
        value = ctypes.c_int(value)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            self._wm_frame,
            rendering_policy,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

    def _set_window_composition_attribute(self, wcad: WindowCompositionAttributeData) -> None:
        ctypes.windll.user32.SetWindowCompositionAttribute(self._wm_frame, wcad)

    def get_preview_disabled(self) -> bool:
        return self._is_preview_disabled

    @windows_only
    def set_preview_disabled(self, is_disabled: bool = False) -> None:
        self._dwm_set_window_attribute(DWMWA_FORCE_ICONIC_REPRESENTATION, int(is_disabled))

        self._is_preview_disabled = is_disabled

    preview_disabled = property(get_preview_disabled, set_preview_disabled)

    @windows_only
    def get_tool_window(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._wm_path, "-toolwindow")

    @windows_only
    def set_tool_window(self, is_toolwindow: bool = False) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", is_toolwindow)

    tool_window = property(get_tool_window, set_tool_window)

    def get_border_color(self) -> Color | None:
        if self._border_color is not None:
            return Color(self._border_color)
        return None

    @windows_only
    def set_border_color(self, color: Color) -> None:
        self._border_color = color = color.hex
        int_color = int(color[5:7] + color[3:5] + color[1:3], 16)
        self._dwm_set_window_attribute(DWMWA_BORDER_COLOR, int_color)

    border_color = property(get_border_color, set_border_color)

    @windows_only
    def set_backdrop_effect(
        self,
        effect: BackdropEffect = BackdropEffect.Blur,
        tint: Color | None = None,
        tint_opacity: float = 0.2,
    ) -> None:
        # https://github.com/Peticali/PythonBlurBehind/blob/main/blurWindow/blurWindow.py
        # https://github.com/sourcechord/FluentWPF/blob/master/FluentWPF/Utility/AcrylicHelper.cs

        build = sys.getwindowsversion().build
        has_mica = build >= 22000
        has_backdrop_type = build >= 22523

        if not has_mica and effect is BackdropEffect.Mica:
            # Mica is available only on Windows 11 build 22000+, fall back to acrylic
            effect == BackdropEffect.Acrylic

        if effect == 0:
            gradient_color = 0

            # Remove `-transparentcolor`
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {{}}")

            # Remove <<Unmaximize>> binding
            self.unbind("<<Unmaximize>>")
        else:
            # Make an ABGR color from `tint` and `tint_opacity`
            # If `tint` is None, use the window background color
            bg_color = Tcl.eval(str, "ttk::style lookup . -background")

            if tint is None:
                res = Tcl.eval((int,), f"winfo rgb . {bg_color}")
                tint = Color(rgb=tuple(value >> 8 for value in res)).hex
            else:
                tint = tint.hex

            tint_alpha = str(hex(int(255 * tint_opacity)))[2:]
            tint_hex_bgr = tint[5:7] + tint[3:5] + tint[1:3]
            gradient_color = int(tint_alpha + tint_hex_bgr, 16)

            # Make the window background, and each pixel with the same colour as the window background fully transparent.
            # These are the areas that will be blurred.
            Tcl.eval(None, f"wm attributes {self._wm_path} -transparentcolor {bg_color}")

            # When the window has `transparentcolor`, the whole window becomes unusable after unmaximizing.
            # Therefore we bind it to the <<Unmaximize>> event (see it below: WindowMixin._generate_state_event),
            # so every time it changes state, it calls the _fullredraw method. See DesktopWindowManager._fullredraw.__doc__ for more.
            self.bind("<<Unmaximize>>", self._fullredraw)

        # Set up AccentPolicy struct
        ap = AccentPolicy()
        ap.AccentFlags = 2  # ACCENT_ENABLE_BLURBEHIND  <- try this with 4 bruhh :D
        ap.AccentState = effect.value
        ap.GradientColor = gradient_color

        # Set up WindowCompositionAttributeData struct
        wcad = WindowCompositionAttributeData()
        wcad.Attribute = 19  # WCA_ACCENT_POLICY
        wcad.Data = ctypes.cast(ctypes.pointer(ap), ctypes.POINTER(ctypes.c_int))
        wcad.SizeOfData = ctypes.sizeof(ap)

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


class WindowMixin(DesktopWindowManager):
    _current_state = "normal"
    _name: str
    _wm_path: str

    def maximize(self) -> None:
        if Tcl.call(str, "tk", "windowingsystem") == "win32":
            Tcl.call(None, "wm", "state", self._wm_path, "zoomed")
        else:
            Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", True)

    def restore(self) -> None:
        state = self.state

        if state in {"hidden", "minimized"}:
            Tcl.call(None, "wm", "deiconify", self._wm_path)
        elif state == "maximized":
            if Tcl.windowing_system == "x11":
                Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", False)
            else:
                Tcl.call(None, "wm", "state", self._wm_path, "normal")
        elif state == "fullscreen":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", False)

    def minimize(self) -> None:
        Tcl.call(None, "wm", "iconify", self._wm_path)

    def fullscreen(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", True)

    def focus(self) -> None:
        Tcl.call(None, "focus", "-force", self._wm_path)

    def group(self, other: WindowMixin) -> None:
        Tcl.call(None, "wm", "group", self._wm_path, other._name)

    def hide(self):
        Tcl.call(None, "wm", "withdraw", self._wm_path)

    def unhide(self):
        Tcl.call(None, "wm", "deiconify", self._wm_path)

    def on_close(self, func: Callable[[WindowMixin], None]) -> Callable[[], None]:
        def wrapper() -> None:
            if func(self):
                self.destroy()

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def state(self):
        try:
            state = Tcl.call(str, "wm", "state", self._wm_path)
        except TclError as e:
            if not Tcl.call(bool, "winfo", "exists", self._wm_path):
                return "closed"
            raise e

        if state == "normal" and Tcl.windowing_system != "x11":  # needs further checking on X11
            return "normal"
        elif state == "iconic":
            return "minimized"
        elif state == "withdrawn":
            return "hidden"
        elif state == "zoomed":
            return "maximized"
        elif Tcl.windowing_system == "x11" and Tcl.call(
            bool, "wm", "attributes", self._wm_path, "-zoomed"
        ):
            return "maximized"
        elif Tcl.call(bool, "wm", "attributes", self._wm_path, "-fullscreen"):
            return "fullscreen"

        return "normal"

    @property
    def is_focused(self) -> int:
        return Tcl.call(str, "focus", "-displayof", self._wm_path)

    @property
    @Tcl.update_before
    def visible(self) -> bool:
        return Tcl.call(bool, "winfo", "ismapped", self._wm_path)

    @property
    def id(self) -> int:
        return int(Tcl.call(str, "winfo", "id", self._wm_path), 16)

    @property
    def _wm_frame(self):
        return int(Tcl.call(str, "wm", "frame", self._wm_path), 16)

    # WM getters, setters

    @Tcl.update_before
    def get_x(self) -> int:
        return Tcl.call(int, "winfo", "x", self._wm_path)

    @Tcl.update_after
    def set_x(self, new_x: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{new_x}+{self.y}")

    x = property(get_x, set_x)

    @Tcl.update_before
    def get_y(self) -> int:
        return Tcl.call(int, "winfo", "y", self._wm_path)

    @Tcl.update_after
    def set_y(self, new_y: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"+{self.x}+{new_y}")

    y = property(get_y, set_y)

    @Tcl.update_before
    def get_width(self) -> int:
        return Tcl.call(int, "winfo", "width", self._wm_path)

    @Tcl.update_after
    def set_width(self, new_width: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{new_width}x{self.height}")

    width = property(get_width, set_width)

    @Tcl.update_before
    def get_height(self) -> int:
        return Tcl.call(int, "winfo", "height", self._wm_path)

    @Tcl.update_after
    def set_height(self, new_height: int) -> None:
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{self.width}x{new_height}")

    height = property(get_height, set_height)

    @Tcl.update_before
    def get_position(self) -> Position:
        return Position(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[2:])
        )

    @Tcl.update_after
    def set_position(self, new_position: Position | tuple[int, int] | int | str) -> None:
        if isinstance(new_position, int):
            new_position = (new_position,) * 2
        elif isinstance(new_position, str):
            from ._info import Screen

            width = self.width
            height = self.height
            screenwidth = Screen._width
            screenheight = Screen._height
            assert screenwidth is not None
            assert screenheight is not None

            if new_position == "center":
                x = screenwidth // 2 - width // 2
                y = screenheight // 2 - height // 2
            elif new_position == "top-left":
                x = y = 0
            elif new_position == "top-right":
                x = screenwidth - width
                y = 0
            elif new_position == "bottom-left":
                x = 0
                y = screenheight - height
            elif new_position == "bottom-right":
                x = screenwidth - width
                y = screenwidth - height

            new_position = (x, y)

        Tcl.call(None, "wm", "geometry", self._wm_path, "+{}+{}".format(*new_position))

    position = property(get_position, set_position)

    @Tcl.update_before
    def get_size(self) -> Size:
        return Size(
            *map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._wm_path))[:2])
        )

    @Tcl.update_after
    def set_size(self, new_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_size, int):
            new_size = (new_size,) * 2

        Tcl.call(None, "wm", "geometry", self._wm_path, "{}x{}".format(*new_size))

    size = property(get_size, set_size)

    @Tcl.update_before
    def get_min_size(self) -> Size:
        return Size(*Tcl.call([str], "wm", "minsize", self._wm_path))

    @Tcl.update_after
    def set_min_size(self, new_min_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_min_size, int):
            new_min_size = (new_min_size,) * 2
        Tcl.call(None, "wm", "minsize", self._wm_path, *new_min_size)

    min_size = property(get_min_size, set_min_size)

    @Tcl.update_before
    def get_max_size(self) -> Size:
        return Size(*Tcl.call([str], "wm", "maxsize", self._wm_path))

    @Tcl.update_after
    def set_max_size(self, new_max_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_max_size, int):
            new_max_size = (new_max_size,) * 2
        Tcl.call(None, "wm", "maxsize", self._wm_path, *new_max_size)

    max_size = property(get_max_size, set_max_size)

    def get_title(self) -> str:
        return Tcl.call(str, "wm", "title", self._wm_path)

    def set_title(self, new_title: str) -> None:
        Tcl.call(None, "wm", "title", self._wm_path, new_title)

    title = property(get_title, set_title)

    def get_always_on_top(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._wm_path, "-topmost")

    def set_always_on_top(self, is_topmost: bool = False) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-topmost", is_topmost)

    always_on_top = property(get_always_on_top, set_always_on_top)

    def get_opacity(self) -> float:
        return Tcl.call(float, "wm", "attributes", self._wm_path, "-alpha")

    def set_opacity(self, alpha: float, wait_till_visible: bool = False) -> None:
        if wait_till_visible:
            Tcl.call(None, "tkwait", "visibility", self._wm_path)
        Tcl.call(None, "wm", "attributes", self._wm_path, "-alpha", alpha)

    opacity = property(get_opacity, set_opacity)

    def get_size_increment(self) -> Size:
        return Size(*Tcl.call([str], "wm", "grid", self._wm_path)[2:])

    def set_size_increment(self, increment: Size | tuple[int, int] | int) -> None:
        if isinstance(increment, int):
            increment = (increment,) * 2
        Tcl.call(None, "wm", "grid", self._wm_path, 1, 1, *increment)

    size_increment = property(get_size_increment, set_size_increment)

    @Tcl.update_before
    def get_aspect_ratio(self) -> None | tuple[Fraction, Fraction]:
        result = Tcl.call((int,), "wm", "aspect", self._wm_path)
        if result == ():
            return None
        return Fraction(*result[:2]), Fraction(*result[2:])

    @Tcl.update_after
    def set_aspect_ratio(
        self,
        new_aspect: tuple[float, float] | tuple[Fraction, Fraction] | float | Fraction | None,
    ) -> None:
        if new_aspect is None:
            return Tcl.call(None, "wm", "aspect", self._wm_path, *("",) * 4)

        if isinstance(new_aspect, (int, float)):
            min = max = new_aspect
        else:
            min, max = new_aspect

        if not isinstance(min, Fraction):
            min = Fraction.from_float(min)

        if not isinstance(max, Fraction):
            max = Fraction.from_float(max)

        Tcl.call(
            None, "wm", "aspect", self._wm_path, *min.as_integer_ratio(), *max.as_integer_ratio()
        )

    aspect_ratio = property(get_aspect_ratio, set_aspect_ratio)

    def get_resizable(self) -> Resizable:
        return Resizable(Tcl.call((bool, bool), "wm", "resizable", self._wm_path))

    def set_resizable(self, directions: Resizable) -> None:
        Tcl.call(None, "wm", "resizable", self._wm_path, *directions.value)

    resizable = property(get_resizable, set_resizable)

    def get_icon(self) -> str:
        return Tcl.call(PIL_TclConverter, "wm", "iconphoto", self._wm_path)

    def set_icon(self, image) -> None:
        Tcl.call(None, "wm", "iconphoto", self._wm_path, image)

    icon = property(get_icon, set_icon)

    def get_on_close_callback(self) -> Callable[[WindowMixin], None]:
        return _commands[Tcl.call(str, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW")]

    def set_on_close_callback(self, callback: Callable[[WindowMixin], None] | None) -> None:
        if callback is None:
            callback = self.destroy

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", callback)

    on_close_callback = property(get_on_close_callback, set_on_close_callback)

    def get_scaling(self) -> float:
        return Tcl.call(float, "tk", "scaling", "-displayof", self._wm_path)

    def set_scaling(self, factor: float) -> None:
        Tcl.call(None, "tk", "scaling", "-displayof", self._wm_path, factor)

    scaling = property(get_scaling, set_scaling)

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


class App(WindowMixin, TkWidget):
    _exists = False
    _name = ".app"
    _wm_path = "."

    def __init__(
        self,
        title: str = "Tukaan window",
        width: int = 200,
        height: int = 200,
    ) -> None:

        TkWidget.__init__(self)

        if App._exists:
            raise TclError("can't create multiple App objects. Use tukaan.Window instead.")
        App._exists = True

        Tcl.init()
        Tcl.eval(None, "pack [ttk::frame .app] -expand 1 -fill both")

        Tcl.call(None, "bind", self._name, "<Map>", self._generate_state_event)
        Tcl.call(None, "bind", self._name, "<Unmap>", self._generate_state_event)
        Tcl.call(None, "bind", self._name, "<Configure>", self._generate_state_event)

        self.set_title(title)
        self.set_size((width, height))

        self.Titlebar = Titlebar(self)
        self.layout: ContainerLayoutManager = ContainerLayoutManager(self)

        # Three different type of pkg initialization, lol
        self._init_tukaan_ext_pkg("Snack")
        self._init_tkdnd()
        load_serif()

        self.theme = native_theme()

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", self.destroy)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is None:
            return self.run()

        raise exc_type(exc_value) from None

    def _init_tukaan_ext_pkg(self, name: str) -> None:
        Tcl.call(None, "lappend", "auto_path", Path(__file__).parent / name / "pkg")
        Tcl.call(None, "package", "require", name)

    def _init_tkdnd(self):
        os = {"Linux": "linux", "Darwin": "mac", "Windows": "win"}[platform.system()]

        if sys.maxsize > 2**32:
            os += "-x64"
        else:
            os += "-x32"

        Tcl.call(None, "lappend", "auto_path", Path(__file__).parent / "tkdnd" / os)
        Tcl.call(None, "package", "require", "tkdnd")

    def destroy(self) -> None:
        """Quit the entire Tcl interpreter"""
        Tcl.call(None, "Snack::audio", "stop")
        Tcl.call(None, "destroy", self._name)
        Tcl.call(None, "destroy", self._wm_path)

        Tcl.quit_interp()

    def run(self) -> None:
        Tcl.main_loop()

    @property
    def user_last_active(self) -> int:
        return Tcl.call(int, "tk", "inactive") / 1000

    @property
    def theme(self) -> Theme | None:
        theme = Tcl.call(str, "ttk::style", "theme", "use")

        if theme in {"vista", "xpnative"}:
            return Win32Theme
        elif theme == "aqua":
            return AquaTheme
        elif theme == "clam":
            return ClamTheme

    @theme.setter
    def theme(self, new_theme: Theme) -> None:
        new_theme._use()


class Window(WindowMixin, BaseWidget):
    _tcl_class = "toplevel"
    _keys = {}
    parent: App | Window

    def __init__(
        self,
        parent: App | Window,
        title: str = "Tukaan window",
        width: int = 200,
        height: int = 200,
    ) -> None:
        if not isinstance(parent, (App, Window)):
            raise TypeError

        BaseWidget.__init__(self, parent)
        self._wm_path = self._name

        self.set_title(title)
        self.set_size((width, height))

        self.Titlebar = Titlebar(self)
        self.layout: ContainerLayoutManager = ContainerLayoutManager(self)

        Tcl.call(None, "bind", self._name, "<Map>", self._generate_state_event)
        Tcl.call(None, "bind", self._name, "<Unmap>", self._generate_state_event)
        Tcl.call(None, "bind", self._name, "<Configure>", self._generate_state_event)

    def wait_till_closed(self):
        Tcl.call(None, "tkwait", "window", self._wm_path)

    def get_modal(self) -> str:
        return bool(Tcl.call(str, "wm", "transient", self._wm_path))

    def set_modal(self, is_modal) -> None:
        if is_modal:
            other = self.parent._wm_path
        else:
            other = ""

        Tcl.call(None, "wm", "transient", self._wm_path, other)

        if Tcl.windowing_system == "aqua":
            Tcl.call(
                "::tk::unsupported::MacWindowStyle", "style", self._wm_path, "moveableModal", ""
            )

    modal = property(get_modal, set_modal)


class _ConfigObject:
    tk_focusFollowsMouse = False

    @property
    def focus_follows_mouse(self) -> None:
        return self.tk_focusFollowsMouse

    @focus_follows_mouse.setter
    def focus_follows_mouse(self, value) -> None:
        if value:
            Tcl.call(None, "tk_focusFollowsMouse")
            self.tk_focusFollowsMouse = True
        else:
            warnings.warn("Config.focus_follows_mouse can't be disabled.")

    @property
    def scaling(self) -> int:
        return Tcl.call(int, "tk", "scaling", "-displayof", ".")

    @scaling.setter
    def scaling(self, factor: int) -> None:
        Tcl.call(None, "tk", "scaling", "-displayof", ".", factor)
