from __future__ import annotations

import functools
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Callable, Sequence

from tukaan._images import Icon
from tukaan._misc import Position, Size
from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan.enums import Resizable, WindowState, WindowType
from tukaan.exceptions import TukaanTclError


class WindowStateManager:
    _wm_path: str

    _current_state = "normal"

    bind: Callable
    unbind: Callable

    def _gen_state_event(self):
        prev_state = self._current_state
        new_state = self.__get_state()

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
            events.append("<<Unmaximize>>")
        elif prev_state == "minimized":
            events.append("<<Unminimize>>")
        elif prev_state == "hidden":
            events.append("<<Unhide>>")
        elif prev_state == "fullscreen":
            events.append("<<Unfullscreen>>")

        for event in events:
            Tcl.eval(None, f"event generate {self._wm_path} {event}")

        self._current_state = new_state

    def __get_state(self) -> str:
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

    def minimize(self) -> None:
        Tcl.call(None, "wm", "iconify", self._wm_path)

    def maximize(self) -> None:
        if Tcl.windowing_system == "x11":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", True)
        else:
            Tcl.call(None, "wm", "state", self._wm_path, "zoomed")

    def go_fullscreen(self) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", True)

    def restore(self) -> None:
        state = self.__get_state()

        if state in {"hidden", "minimized"}:
            Tcl.call(None, "wm", "deiconify", self._wm_path)
        elif state == "maximized":
            if Tcl.windowing_system == "x11":
                Tcl.call(None, "wm", "attributes", self._wm_path, "-zoomed", False)
            else:
                Tcl.call(None, "wm", "state", self._wm_path, "normal")
        elif state == "fullscreen":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-fullscreen", False)

    def hide(self) -> None:
        Tcl.call(None, "wm", "withdraw", self._wm_path)

    def unhide(self) -> None:
        Tcl.call(None, "wm", "deiconify", self._wm_path)

    def focus(self) -> None:
        Tcl.call(None, "focus", "-force", self._wm_path)

    @property
    def state(self) -> WindowState:
        return WindowState(self.__get_state())

    @property
    def focused(self) -> bool:
        return Tcl.call(str, "focus", "-displayof", self._wm_path) == self._wm_path

    @property
    @Tcl.redraw_before
    def visible(self) -> bool:
        return Tcl.call(bool, "winfo", "viewable", self._wm_path)

    @property
    def always_on_top(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._wm_path, "-topmost")

    @always_on_top.setter
    def always_on_top(self, value: bool) -> None:
        Tcl.call(None, "wm", "attributes", self._wm_path, "-topmost", value)


class WindowGeometryManager:
    _wm_path: str

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
        return Resizable(Tcl.call((str,), "wm", "resizable", self._wm_path))

    @resizable.setter
    def resizable(self, value: Resizable) -> None:
        Tcl.call(None, "wm", "resizable", self._wm_path, *value.value)


class WindowDecorationManager:
    """Stuff that isn't necessarily related to the window decoration, but is part of the 'eye-candy'"""

    _wm_path: str
    _icon: Icon | Path | None = None

    @property
    @Platform.windows_only
    def use_dark_mode_decorations(self) -> None:
        ...

    @use_dark_mode_decorations.setter
    @Platform.windows_only
    def use_dark_mode_decorations(self, value: bool) -> None:
        import ctypes.windll  # type: ignore

        if sys.getwindowsversion().build < 22000:
            return

        c_value = ctypes.c_int(int(value))

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(Tcl.call(str, "wm", "frame", self._wm_path), 16),
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.byref(c_value),
            ctypes.sizeof(ctypes.c_int),
        )

    @property
    def title(self) -> str:
        return Tcl.call(str, "wm", "title", self._wm_path)

    @title.setter
    def title(self, value: str) -> None:
        Tcl.call(None, "wm", "title", self._wm_path, value)

    @property
    def opacity(self) -> float:
        return Tcl.call(float, "wm", "attributes", self._wm_path, "-alpha")

    @opacity.setter
    def opacity(self, value: float) -> None:
        if Tcl.windowing_system == "x11":
            Tcl.call(None, "tkwait", "visibility", self._wm_path)

        Tcl.call(None, "wm", "attributes", self._wm_path, "-alpha", value)


class WindowManager(WindowGeometryManager, WindowStateManager, WindowDecorationManager):
    _name: str
    destroy: Callable[[], None]

    @property
    def type(self) -> WindowType:
        """
        Sets the purpose of this window. Most window managers use this property
        to appropriately set decorations and animations for the window.

        For example a utility window usually only has a close button, and a
        splash window would be placed in the center of the screen, without decorations.
        """
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
            if value is WindowType.Utility:
                Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", True)
            elif value is WindowType.Normal:
                Tcl.call(None, "wm", "attributes", self._wm_path, "-toolwindow", False)
        elif Tcl.windowing_system == "x11":
            Tcl.call(None, "wm", "attributes", self._wm_path, value)

    def group(self, other: WindowManager) -> None:
        Tcl.call(None, "wm", "group", self._wm_path, other._wm_path)

    def on_close(self, func: Callable[[WindowManager], None]) -> Callable[[], None]:
        @functools.wraps(func)
        def wrapper() -> None:
            if func(self):
                self.destroy()

        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def id(self) -> int:
        return int(Tcl.call(str, "winfo", "id", self._wm_path), 16)

    @property
    def hwnd(self) -> int:
        return int(Tcl.call(str, "wm", "frame", self._wm_path), 16)

    @property
    def class_name(self) -> int:
        return Tcl.call(str, "winfo", "class", self._wm_path)
