from __future__ import annotations

import functools
import re
from fractions import Fraction
from typing import Callable, Sequence

from tukaan._data import Position, Size
from tukaan._images import Icon
from tukaan._tcl import Tcl
from tukaan.enums import Resizable, WindowState, WindowType
from tukaan.exceptions import TukaanTclError


class WindowManager:
    _wm_path: str

    def _get_state(self) -> str:
        try:
            state = Tcl.call(str, "wm", "state", self._wm_path)
        except TukaanTclError as e:
            # FIXME: what if interpreter is destroyed?
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
        # fmt: off
        elif (
            Tcl.windowing_system == "x11"
            and Tcl.call(bool, "wm", "attributes", self._wm_path, "-zoomed")
        ):
            return "maximized"
        # fmt: on
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
        value: tuple[float, float] | tuple[Fraction, Fraction] | float | Fraction | None,
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
