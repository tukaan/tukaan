from __future__ import annotations

import ctypes
import os
import platform
import re
import sys
from collections import namedtuple
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Optional

import _tkinter as tk

from ._base import BaseWidget, TkWidget
from ._constants import _resizable
from ._images import _image_converter_class
from ._layouts import BaseLayoutManager
from ._misc import Color
from ._utils import _callbacks, from_tcl, reversed_dict, to_tcl, windows_only
from .exceptions import ApplicationError, TclError

tcl_interp = None
tkdnd_inited = False

Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])


def updated(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        self._tcl_call(None, "update", "idletasks")
        result = func(self, *args, **kwargs)
        self._tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def update_before(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        self._tcl_call(None, "update", "idletasks")
        return func(self, *args, **kwargs)

    return wrapper


def update_after(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        self._tcl_call(None, "update", "idletasks")
        return result

    return wrapper


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
    _tcl_call: Callable
    _tcl_eval: Callable
    wm_path: str

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
    _tcl_call: Callable
    _tcl_eval: Callable
    bind: Callable
    minimize: Callable
    restore: Callable
    unbind: Callable
    _wm_frame: int
    wm_path: str

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
        return self._tcl_call(bool, "wm", "attributes", self.wm_path, "-toolwindow")

    @windows_only
    def set_tool_window(self, is_toolwindow: bool = False) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-toolwindow", is_toolwindow)

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
        effect: str = "blur",
        tint: Optional[Color] = None,
        tint_opacity: float = 0.2,
    ) -> None:
        # https://github.com/Peticali/PythonBlurBehind/blob/main/blurWindow/blurWindow.py
        # https://github.com/sourcechord/FluentWPF/blob/master/FluentWPF/Utility/AcrylicHelper.cs

        effect = {
            None: 0,
            "opaque-color": 1,
            "transparent-color": 2,
            "blur": 3,
            "acrylic": 4,
            "mica": 5,
        }[effect]

        build = sys.getwindowsversion().build
        has_mica = build >= 22000
        has_backdrop_type = build >= 22523

        if not has_mica and effect == 5:
            # Mica is available only on Windows 11 build 22000+, fall back to acrylic
            effect = 4

        if effect == 0:
            gradient_color = 0

            # Remove `-transparentcolor`
            self._tcl_eval(None, f"wm attributes {self.wm_path} -transparentcolor {{}}")

            # Remove <<Unmaximize>> binding
            self.unbind("<<Unmaximize>>")
        else:
            # Make an ABGR color from `tint` and `tint_opacity`
            # If `tint` is None, use the window background color
            bg_color = self._tcl_eval(str, "ttk::style lookup . -background")

            if tint is None:
                res = self._tcl_eval((int,), f"winfo rgb . {bg_color}")
                tint = Color(rgb=tuple(value >> 8 for value in res)).hex
            else:
                tint = tint.hex

            tint_alpha = str(hex(int(255 * tint_opacity)))[2:]
            tint_hex_bgr = tint[5:7] + tint[3:5] + tint[1:3]
            gradient_color = int(tint_alpha + tint_hex_bgr, 16)

            # Make the window background, and each pixel with the same colour as the window background fully transparent.
            # These are the areas that will be blurred.
            self._tcl_eval(None, f"wm attributes {self.wm_path} -transparentcolor {bg_color}")

            # When the window has `transparentcolor`, the whole window becomes unusable after unmaximizing.
            # Therefore we bind it to the <<Unmaximize>> event (see it below: TkWindowManager._generate_state_event),
            # so every time it changes state, it calls the _fullredraw method. See DesktopWindowManager._fullredraw.__doc__ for more.
            self.bind("<<Unmaximize>>", self._fullredraw)

        # Set up AccentPolicy struct
        ap = AccentPolicy()
        ap.AccentFlags = 2  # ACCENT_ENABLE_BLURBEHIND  <- try this with 4 bruhh :D
        ap.AccentState = effect
        ap.GradientColor = gradient_color

        # Set up WindowCompositionAttributeData struct
        wcad = WindowCompositionAttributeData()
        wcad.Attribute = 19  # WCA_ACCENT_POLICY
        wcad.Data = ctypes.cast(ctypes.pointer(ap), ctypes.POINTER(ctypes.c_int))
        wcad.SizeOfData = ctypes.sizeof(ap)

        self._set_window_composition_attribute(wcad)

        if effect == 5:
            if has_backdrop_type:
                # https://github.com/minusium/MicaForEveryone/blob/master/MicaForEveryone.Win32/PInvoke/DWM_SYSTEMBACKDROP_TYPE.cs
                # Mica effect is 2
                self._dwm_set_window_attribute(DWMWA_SYSTEMBACKDROP_TYPE, 2)
            elif has_mica:
                self._dwm_set_window_attribute(DWMWA_MICA_EFFECT, 1)
        elif effect == 0:
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


class TkWindowManager(DesktopWindowManager):
    _tcl_call: Callable
    _tcl_eval: Callable
    _winsys: str
    tcl_path: str
    wm_path: str

    def maximize(self) -> None:
        if self._tcl_call(str, "tk", "windowingsystem") == "win32":
            self._tcl_call(None, "wm", "state", self.wm_path, "zoomed")
        else:
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", True)

    def restore(self) -> None:
        state = self.state

        if state in {"hidden", "minimized"}:
            self._tcl_call(None, "wm", "deiconify", self.wm_path)
        elif state == "maximized":
            if self._winsys == "x11":
                self._tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", False)
            else:
                self._tcl_call(None, "wm", "state", self.wm_path, "normal")
        elif state == "fullscreen":
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-fullscreen", False)

    def minimize(self) -> None:
        self._tcl_call(None, "wm", "iconify", self.wm_path)

    def fullscreen(self) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-fullscreen", True)

    def focus(self) -> None:
        self._tcl_call(None, "focus", "-force", self.wm_path)

    def group(self, other: TkWindowManager) -> None:
        self._tcl_call(None, "wm", "group", self.wm_path, other.tcl_path)

    def hide(self):
        self._tcl_call(None, "wm", "withdraw", self.wm_path)

    def unhide(self):
        self._tcl_call(None, "wm", "deiconify", self.wm_path)

    def on_close(self, func: Callable[[TkWindowManager], None]) -> Callable[[], None]:
        def wrapper() -> None:
            if func(self):
                self.destroy()

        self._tcl_call(None, "wm", "protocol", self.wm_path, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def state(self):
        try:
            state = self._tcl_call(str, "wm", "state", self.wm_path)
        except TclError as e:
            if not self._tcl_call(bool, "winfo", "exists", self.wm_path):
                return "closed"
            raise e

        if state == "iconic":
            return "minimized"
        elif state == "withdrawn":
            return "hidden"
        elif state == "zoomed":
            return "maximized"
        elif self._winsys == "x11" and self._tcl_call(
            bool, "wm", "attributes", self.wm_path, "-zoomed"
        ):
            return "maximized"
        elif self._tcl_call(bool, "wm", "attributes", self.wm_path, "-fullscreen"):
            return "fullscreen"

        return "normal"

    @property
    def is_focused(self) -> int:
        return self._tcl_call(str, "focus", "-displayof", self.wm_path)

    @property
    def id(self) -> int:
        return int(self._tcl_call(str, "winfo", "id", self.wm_path), 16)

    @property
    def _wm_frame(self):
        return int(self._tcl_call(str, "wm", "frame", self.wm_path), 16)

    # WM getters, setters

    @update_before
    def get_x(self) -> int:
        return self._tcl_call(int, "winfo", "x", self.wm_path)

    @update_after
    def set_x(self, new_x: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"+{new_x}+{self.y}")

    x = property(get_x, set_x)

    @update_before
    def get_y(self) -> int:
        return self._tcl_call(int, "winfo", "y", self.wm_path)

    @update_after
    def set_y(self, new_y: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"+{self.x}+{new_y}")

    y = property(get_y, set_y)

    @update_before
    def get_width(self) -> int:
        return self._tcl_call(int, "winfo", "width", self.wm_path)

    @update_after
    def set_width(self, new_width: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{new_width}x{self.height}")

    width = property(get_width, set_width)

    @update_before
    def get_height(self) -> int:
        return self._tcl_call(int, "winfo", "height", self.wm_path)

    @update_after
    def set_height(self, new_height: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{self.width}x{new_height}")

    height = property(get_height, set_height)

    @update_before
    def get_position(self) -> Position:
        return Position(
            *map(int, re.split(r"x|\+", self._tcl_call(str, "wm", "geometry", self.wm_path))[2:])
        )

    @update_after
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

        self._tcl_call(None, "wm", "geometry", self.wm_path, "+{}+{}".format(*new_position))

    position = property(get_position, set_position)

    @update_before
    def get_size(self) -> Size:
        return Size(
            *map(int, re.split(r"x|\+", self._tcl_call(str, "wm", "geometry", self.wm_path))[:2])
        )

    @update_after
    def set_size(self, new_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_size, int):
            new_size = (new_size,) * 2
        self._tcl_call(None, "wm", "geometry", self.wm_path, "{}x{}".format(*new_size))

    size = property(get_size, set_size)

    @update_before
    def get_min_size(self) -> Size:
        return Size(*self._tcl_call([str], "wm", "minsize", self.wm_path))

    @update_after
    def set_min_size(self, new_min_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_min_size, int):
            new_min_size = (new_min_size,) * 2
        self._tcl_call(None, "wm", "minsize", self.wm_path, *new_min_size)

    min_size = property(get_min_size, set_min_size)

    @update_before
    def get_max_size(self) -> Size:
        return Size(*self._tcl_call([str], "wm", "maxsize", self.wm_path))

    @update_after
    def set_max_size(self, new_max_size: Size | tuple[int, int] | int) -> None:
        if isinstance(new_max_size, int):
            new_max_size = (new_max_size,) * 2
        self._tcl_call(None, "wm", "maxsize", self.wm_path, *new_max_size)

    max_size = property(get_max_size, set_max_size)

    def get_title(self) -> str:
        return self._tcl_call(str, "wm", "title", self.wm_path)

    def set_title(self, new_title: str) -> None:
        self._tcl_call(None, "wm", "title", self.wm_path, new_title)

    title = property(get_title, set_title)

    def get_always_on_top(self) -> bool:
        return self._tcl_call(bool, "wm", "attributes", self.wm_path, "-topmost")

    def set_always_on_top(self, is_topmost: bool) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-topmost", is_topmost)

    always_on_top = property(get_always_on_top, set_always_on_top)

    def get_opacity(self) -> float:
        return self._tcl_call(float, "wm", "attributes", self.wm_path, "-alpha")

    def set_opacity(self, alpha: float, wait_till_visible: bool = False) -> None:
        if wait_till_visible:
            self._tcl_call(None, "tkwait", "visibility", self.wm_path)
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-alpha", alpha)

    opacity = property(get_opacity, set_opacity)

    def get_size_increment(self) -> Size:
        return Size(*self._tcl_call([str], "wm", "grid", self.wm_path)[2:])

    def set_size_increment(self, increment: Size | tuple[int, int] | int) -> None:
        if isinstance(increment, int):
            increment = (increment,) * 2
        self._tcl_call(None, "wm", "grid", self.wm_path, 1, 1, *increment)

    size_increment = property(get_size_increment, set_size_increment)

    @update_before
    def get_aspect_ratio(self) -> None | tuple[Fraction, Fraction]:
        result = self._tcl_call((int,), "wm", "aspect", self.wm_path)
        if result == ():
            return None
        return Fraction(*result[:2]), Fraction(*result[2:])

    @update_after
    def set_aspect_ratio(
        self,
        new_aspect: Optional[tuple[float, float] | tuple[Fraction, Fraction] | float | Fraction],
    ) -> None:
        if new_aspect is None:
            return self._tcl_call(None, "wm", "aspect", self.wm_path, *("",) * 4)

        if isinstance(new_aspect, (int, float)):
            min = max = new_aspect
        else:
            min, max = new_aspect

        if not isinstance(min, Fraction):
            min = Fraction.from_float(min)

        if not isinstance(max, Fraction):
            max = Fraction.from_float(max)

        self._tcl_call(
            None, "wm", "aspect", self.wm_path, *min.as_integer_ratio(), *max.as_integer_ratio()
        )

    aspect_ratio = property(get_aspect_ratio, set_aspect_ratio)

    def get_resizable(self) -> str:
        return reversed_dict(_resizable)[
            self._tcl_call((bool, bool), "wm", "resizable", self.wm_path)
        ]

    def set_resizable(self, directions: str) -> None:
        self._tcl_call(None, "wm", "resizable", self.wm_path, *_resizable[directions])

    resizable = property(get_resizable, set_resizable)

    def get_icon(self) -> str:
        return self._tcl_call(_image_converter_class, "wm", "iconphoto", self.wm_path)

    def set_icon(self, image) -> None:
        self._tcl_call(None, "wm", "iconphoto", self.wm_path, image)

    icon = property(get_icon, set_icon)

    def get_on_close_callback(self) -> Callable[[TkWindowManager], None]:
        return _callbacks[self._tcl_call(str, "wm", "protocol", self.wm_path, "WM_DELETE_WINDOW")]

    def set_on_close_callback(self, callback: Optional[Callable[[TkWindowManager], None]]) -> None:
        if callback is None:
            callback = self.destroy

        self._tcl_call(None, "wm", "protocol", self.wm_path, "WM_DELETE_WINDOW", callback)

    on_close_callback = property(get_on_close_callback, set_on_close_callback)

    def get_scaling(self) -> float:
        return self._tcl_call(float, "tk", "scaling", "-displayof", self.wm_path)

    def set_scaling(self, factor: float) -> None:
        self._tcl_call(None, "tk", "scaling", "-displayof", self.wm_path, factor)

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


class App(TkWindowManager, TkWidget):
    wm_path = "."
    tcl_path = ".app"

    def __init__(
        self,
        title: str = "Tukaan window",
        width: int = 200,
        height: int = 200,
    ) -> None:

        TkWidget.__init__(self)

        global tcl_interp
        if tcl_interp is self:
            raise TclError("can't create multiple App objects. Use tukaan.Window instead.")
        tcl_interp = self

        self.app = tk.create(
            None, os.path.basename(sys.argv[0]), "Tukaan window", True, True, True, False, None
        )

        self.app.loadtk()
        self._winsys = self._tcl_call(str, "tk", "windowingsystem").lower()
        self.tcl_interp_address = self.app.interpaddr()  # only for PIL

        self.layout: BaseLayoutManager = BaseLayoutManager(self)

        self._tcl_eval(None, "pack [ttk::frame .app] -expand 1 -fill both")

        self.title = title
        self.size = width, height
        self.Titlebar = Titlebar(self)

        self._current_state = "normal"
        self._tcl_call(None, "bind", self.tcl_path, "<Map>", self._generate_state_event)
        self._tcl_call(None, "bind", self.tcl_path, "<Unmap>", self._generate_state_event)
        self._tcl_call(None, "bind", self.tcl_path, "<Configure>", self._generate_state_event)

        self._init_tkdnd()
        self._init_tkextrafont()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is None:
            return self.run()
        raise exc_type(exc_value) from None

    def _tcl_call(self, return_type: Any, *args) -> Any:
        try:
            result = self.app.call(*map(to_tcl, args))
            if return_type is None:
                return
            return from_tcl(return_type, result)

        except tk.TclError as e:
            msg = str(e)

            if "application has been destroyed" in msg:
                raise ApplicationError("can't invoke Tcl callback. Application has been destroyed.")

            if msg.startswith("couldn't read file"):
                # FileNotFoundError is a bit more pythonic than TclError: couldn't read file
                path = msg.split('"')[1]  # path is between ""
                sys.tracebacklimit = 0
                raise FileNotFoundError(f"No such file or directory: {path!r}") from None
            else:
                raise TclError(msg) from None

    def _tcl_eval(self, return_type: Any, code: str) -> Any:
        try:
            result = self.app.eval(code)
        except tk.TclError:
            raise TclError
        else:
            return from_tcl(return_type, result)

    def _get_boolean(self, arg) -> bool:
        return self.app.getboolean(arg)

    def _get_string(self, obj) -> str:
        if isinstance(obj, str):
            return obj

        if isinstance(obj, tk.Tcl_Obj):
            return obj.string

        return self._tcl_call(str, "format", obj)

    def _split_list(self, arg) -> tuple:
        return self.app.splitlist(arg)

    def _lappend_auto_path(self, path: str | Path):
        self._tcl_call(None, "lappend", "auto_path", path)

    @property
    def _auto_path(self):
        return self._tcl_call([str], "set", "auto_path")

    def _init_tkdnd(self):
        os = {"Linux": "linux", "Darwin": "mac", "Windows": "win"}[platform.system()]

        if sys.maxsize > 2**32:
            os += "-x64"
        else:
            os += "-x32"

        self._lappend_auto_path(Path(__file__).parent / "tkdnd" / os)
        self._tcl_call(None, "package", "require", "tkdnd")

    def _init_tkextrafont(self):
        self._lappend_auto_path(Path(__file__).parent / "tkextrafont")
        self._tcl_call(None, "package", "require", "extrafont")

    def run(self) -> None:
        self.app.mainloop(0)

    def destroy(self) -> None:
        """Quit the entire Tcl interpreter"""

        global tcl_interp

        self._tcl_call(None, "destroy", self.tcl_path)
        self._tcl_call(None, "destroy", self.wm_path)

        tcl_interp = None

        self.app.quit()

    def focus_should_follow_mouse(self) -> None:
        self._tcl_call(None, "tk_focusFollowsMouse")

    @property
    def user_last_active(self) -> int:
        return self._tcl_call(int, "tk", "inactive") / 1000

    def _get_theme_aliases(self) -> dict[str, str]:
        theme_dict = {"clam": "clam", "legacy": "default", "native": "clam"}

        if self._winsys == "win32":
            theme_dict["native"] = "vista"
        elif self._winsys == "aqua":
            theme_dict["native"] = "aqua"

        return theme_dict

    @property
    def theme(self) -> str:
        theme_dict = {"clam": "clam", "default": "legacy", "vista": "native", "aqua": "native"}

        try:
            return theme_dict[self._tcl_call(str, "ttk::style", "theme", "use")]
        except KeyError:
            return self._tcl_call(str, "ttk::style", "theme", "use")

    @theme.setter
    def theme(self, theme) -> None:
        self._tcl_call(None, "ttk::style", "theme", "use", self._get_theme_aliases()[theme])


class Window(TkWindowManager, BaseWidget):
    _tcl_class = "toplevel"
    _keys = {}
    parent: App | Window

    def __init__(self, parent: Optional[App | Window] = None) -> None:
        if not isinstance(parent, (App, Window)) and parent is not None:
            raise RuntimeError

        BaseWidget.__init__(self, parent)
        self.wm_path = self.tcl_path
        self._winsys = self.parent._winsys
        self.Titlebar = Titlebar(self)

        self._current_state = "normal"
        self._tcl_call(None, "bind", self.tcl_path, "<Map>", self._generate_state_event)
        self._tcl_call(None, "bind", self.tcl_path, "<Unmap>", self._generate_state_event)
        self._tcl_call(None, "bind", self.tcl_path, "<Configure>", self._generate_state_event)

    def wait_till_closed(self):
        self._tcl_call(None, "tkwait", "window", self.wm_path)

    def get_modal(self) -> str:
        return bool(self._tcl_call(str, "wm", "transient", self.wm_path))

    def set_modal(self, is_modal) -> None:
        if is_modal:
            other = self.parent.wm_path
        else:
            other = ""

        self._tcl_call(None, "wm", "transient", self.wm_path, other)

        if self._winsys == "aqua":
            self._tcl_call(
                "::tk::unsupported::MacWindowStyle", "style", self.wm_path, "moveableModal", ""
            )

    modal = property(get_modal, set_modal)
