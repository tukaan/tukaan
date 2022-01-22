from __future__ import annotations

import os
import re
import sys
from collections import namedtuple
from typing import Any, Callable, Optional
from fractions import Fraction

import _tkinter as tk

from ._base import BaseWidget, TkWidget
from ._constants import _resizable
from ._images import _image_converter_class
from ._layouts import BaseLayoutManager
from ._utils import from_tcl, reversed_dict, to_tcl
from .exceptions import TclError

tcl_interp = None

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


class WindowManager:
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
        state = self._tcl_call(str, "wm", "state", self.wm_path)

        if state in {"iconic", "withdrawn"}:
            self._tcl_call(None, "wm", "deiconify", self.wm_path)

        elif state == "zoomed":
            self._tcl_call(None, "wm", "state", self.wm_path, "normal")

        elif self._winsys == "x11" and self._tcl_call(
            bool, "wm", "attributes", self.wm_path, "-zoomed"
        ):
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", False)

        elif self._tcl_call(bool, "wm", "attributes", self.wm_path, "-fullscreen"):
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-fullscreen", False)

    def minimize(self) -> None:
        self._tcl_call(None, "wm", "iconify", self.wm_path)

    def fullscreen(self) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-fullscreen", True)

    def focus(self) -> None:
        self._tcl_call(None, "focus", "-force", self.wm_path)

    def group(self, other: WindowManager) -> None:
        self._tcl_call(None, "wm", "group", self.wm_path, other.tcl_path)

    @property
    def in_focus(self) -> int:
        return self._tcl_call(str, "focus", "-displayof", self.wm_path)

    @property
    def id(self) -> int:
        return int(self._tcl_call(str, "winfo", "id", self.wm_path), 0)

    # WM getters, setters

    @update_before
    def get_x(self) -> int:
        return self._tcl_call(int, "winfo", "x", self.wm_path)

    @update_after
    def set_x(self, x: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"+{x}+{self.y}")

    x = property(get_x, set_x)

    @update_before
    def get_y(self) -> int:
        return self._tcl_call(int, "winfo", "y", self.wm_path)

    @update_after
    def set_y(self, y: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"+{self.x}+{y}")

    y = property(get_y, set_y)

    @update_before
    def get_width(self) -> int:
        return self._tcl_call(int, "winfo", "width", self.wm_path)

    @update_after
    def set_width(self, width: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{width}x{self.height}")

    width = property(get_width, set_width)

    @update_before
    def get_height(self) -> int:
        return self._tcl_call(int, "winfo", "height", self.wm_path)

    @update_after
    def set_height(self, height: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{self.width}x{height}")

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
            from ._misc import Screen

            width = self.width
            height = self.height
            screenwidth = Screen._width
            screenheight = Screen._height

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
        return self._tcl_call(None, "wm", "title", self.wm_path)

    def set_title(self, new_title: str = None) -> None:
        self._tcl_call(None, "wm", "title", self.wm_path, new_title)

    title = property(get_title, set_title)

    def get_topmost(self) -> bool:
        return self._tcl_call(bool, "wm", "attributes", self.wm_path, "-topmost")

    def set_topmost(self, is_topmost: bool = False) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-topmost", is_topmost)

    topmost = property(get_topmost, set_topmost)

    def get_opacity(self) -> float:
        return self._tcl_call(float, "wm", "attributes", self.wm_path, "-alpha")

    def set_opacity(self, alpha: float) -> None:
        self._tcl_call(None, "tkwait", "visibility", self.wm_path)
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-alpha", "alpha")

    opacity = property(get_opacity, set_opacity)

    def get_size_increment(self) -> Size:
        return Size(*self._tcl_call([str], "wm", "grid", self.wm_path)[2:])

    def set_size_increment(self, increment: Size | tuple[int, int] | int) -> None:
        if isinstance(increment, int):
            increment = (increment,) * 2
        self._tcl_call(None, "wm", "grid", self.wm_path, 1, 1, *increment)

    size_increment = property(get_size_increment, set_size_increment)

    @update_before
    def get_aspect_ratio(self) -> tuple[Fraction, Fraction]:
        result = self._tcl_call((int,), "wm", "aspect", self.wm_path)
        if result == ():
            return None
        return Fraction(*result[:2]), Fraction(*result[2:])

    @update_after
    def set_aspect_ratio(self, new_aspect: tuple[float, float] | float | None) -> None:
        if new_aspect is None:
            self._tcl_call(None, "wm", "aspect", self.wm_path, *("",) * 4)
            return

        if isinstance(new_aspect, (int, float)):
            min = max = new_aspect
        else:
            min, max = new_aspect

        if isinstance(min, Fraction):
            min_numer, min_denom = min.as_integer_ratio()
        else:
            min_numer, min_denom = Fraction.from_float(min).as_integer_ratio()

        if isinstance(min, Fraction):
            max_numer, max_denom = max.as_integer_ratio()
        else:
            max_numer, max_denom = Fraction.from_float(max).as_integer_ratio()

        self._tcl_call(
            None, "wm", "aspect", self.wm_path, min_numer, min_denom, max_numer, max_denom
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

    def get_on_close(self) -> str:
        return self._tcl_call(str, "wm", "protocol", self.wm_path, "WM_DELETE_WINDOW")

    def set_on_close(self, image) -> None:
        self._tcl_call(None, "wm", "protocol", self.wm_path, "WM_DELETE_WINDOW", image)

    on_close = property(get_on_close, set_on_close)

    # Platform specific things

    def _dwm_set_window_attribute(self, rendering_policy, value):
        """
        Windows only feature

        The idea of these windll and dwm stuff came from this Gist by Olikonsti:
        https://gist.github.com/Olikonsti/879edbf69b801d8519bf25e804cec0aa
        """

        from ctypes import windll, c_int, byref, sizeof

        value = c_int(value)

        windll.dwmapi.DwmSetWindowAttribute(
            windll.user32.GetParent(self.id), rendering_policy, byref(value), sizeof(value)
        )

    @property
    def immersive_dark_mode(self):
        return self._is_immersive_dark_mode_used

    @immersive_dark_mode.setter
    @update_before
    def immersive_dark_mode(self, is_used=False):
        rendering_policy = 20  # DWMWA_USE_IMMERSIVE_DARK_MODE

        self._dwm_set_window_attribute(rendering_policy, int(is_used))

        self._is_immersive_dark_mode_used = is_used

        # Need to redraw the titlebar
        self.minimize()
        self.restore()

    @property
    def rtl_titlebar(self):
        return self._is_rtl_titlebar_used

    @rtl_titlebar.setter
    @update_before
    def rtl_titlebar(self, is_used=False):
        rendering_policy = 6  # DWMWA_NONCLIENT_RTL_LAYOUT

        self._dwm_set_window_attribute(rendering_policy, int(is_used))

        self._is_rtl_titlebar_used = is_used

    @property
    def preview_disabled(self):
        return self._is_preview_disabled

    @preview_disabled.setter
    @update_before
    def preview_disabled(self, is_disabled=False):
        rendering_policy = 7  # DWMWA_FORCE_ICONIC_REPRESENTATION

        self._dwm_set_window_attribute(rendering_policy, int(is_disabled))

        self._is_preview_disabled = is_disabled


class App(WindowManager, TkWidget):
    wm_path = "."
    tcl_path = ".app"

    def __init__(
        self,
        title: str = "Tukaan window",
        width: int = 200,
        height: int = 200,
        theme: str = "native",
    ) -> None:

        TkWidget.__init__(self)

        global tcl_interp
        if tcl_interp is self:
            raise TclError("can't create multiple App objects use a Window instead")
        tcl_interp = self

        self.app = tk.create(
            None, os.path.basename(sys.argv[0]), "Tukaan window", True, True, True, False, None
        )

        self.app.loadtk()
        self._winsys = self._tcl_call(str, "tk", "windowingsystem").lower()
        self.tcl_interp_address = self.app.interpaddr()  # only for PIL

        self.layout: BaseLayoutManager = BaseLayoutManager(self)

        self._tcl_call(None, "ttk::frame", ".app")
        self._tcl_call(None, "pack", ".app", "-expand", "1", "-fill", "both")

        self.title = title
        self.size = width, height
        self.theme = theme

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
        
        except tk.TclError as msg:
            msg = str(msg)

            if msg.startswith("couldn't read file"):
                # FileNotFoundError is a bit more pythonic than TclError: couldn't read file
                path = msg.split('"')[1]  # path is between ""
                sys.tracebacklimit = 0
                raise FileNotFoundError(f"No such file or directory: {path!r}") from None
            else:
                raise TclError(msg) from None

    def _tcl_eval(self, return_type: Any, code: str) -> Any:
        result = self.app.eval(code)
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

    def run(self) -> None:
        self.app.mainloop(0)

    def quit(self) -> None:
        # There is no App.destroy, only App.quit,
        # which also quits the entire tcl interpreter

        global tcl_interp

        for child in tuple(self._children.values()):
            child.destroy()

        self._tcl_call(None, "destroy", self.tcl_path)
        self._tcl_call(None, "destroy", self.wm_path)

        tcl_interp = None

        self.app.quit()

    @property
    def user_last_active(self) -> int:
        return self._tcl_call(int, "tk", "inactive") / 1000

    def focus_should_follow_mouse(self) -> int:
        self._tcl_call(None, "tk_focusFollowsMouse")

    @property
    def scaling(self) -> int:
        return self._tcl_call(int, "tk", "scaling", "-displayof", ".")

    @scaling.setter
    def scaling(self, factor: int) -> None:
        self._tcl_call(None, "tk", "scaling", "-displayof", ".", factor)

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


class Window(WindowManager, BaseWidget):
    _tcl_class = "toplevel"
    _keys = {}

    def __init__(self, parent: Optional[TkWidget] = None) -> None:
        BaseWidget.__init__(self, parent)
        self.wm_path = self.tcl_path
