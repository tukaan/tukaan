from __future__ import annotations

import re
from typing import Any, Callable, Literal, cast

from ._constants import _window_pos
from ._platform import Platform
from .exceptions import TclError

# This module can't use anything that relies on get_tcl_interp,
# so it has its own each of those, which isn't a good thing (update decoratos) :(


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


class WindowMixin:
    _tcl_call: Callable
    wm_path: str
    tcl_path: str

    def maximize(self) -> None:
        if self._tcl_call(None, "tk", "windowingsystem") == "win32":
            self._tcl_call(None, "wm", "state", self.wm_path, "zoomed")
        else:
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", True)

    def restore(self) -> None:
        if self._tcl_call(None, "tk", "windowingsystem") == "win32":
            self._tcl_call(None, "wm", "state", self.wm_path, "normal")
        else:
            self._tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", False)

    def iconify(self) -> None:
        self._tcl_call(None, "wm", "iconify", self.wm_path)

    def deiconify(self) -> None:
        self._tcl_call(None, "wm", "deiconify", self.wm_path)

    @property
    def fullscreen(self) -> bool:
        return self._tcl_call(bool, "wm", "attributes", self.wm_path, "-fullscreen")

    @fullscreen.setter
    def fullscreen(self, is_fullscreen) -> None:
        # todo: bind f11
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-fullscreen", is_fullscreen)

    @property  # type: ignore
    @update_before
    def size(self) -> tuple[int, int]:
        return cast(
            tuple[int, int],
            tuple(
                map(
                    int,
                    re.split(r"x|\+", self._tcl_call(str, "wm", "geometry", self.wm_path))[:2],
                )
            ),
        )

    @size.setter  # type: ignore
    @update_after
    def size(self, size: int | tuple[int, int] | list[int]) -> None:
        if isinstance(size, int):
            width = height = size
        elif isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        else:
            raise RuntimeError
        width, height = tuple(
            map(
                lambda a: self._tcl_call(int, "winfo", "pixels", ".", a),
                (width, height),
            )
        )
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{width}x{height}")

    @property  # type: ignore
    @update_before
    def position(self) -> tuple[int, int]:
        return cast(
            tuple[int, int],
            tuple(
                map(
                    int,
                    re.split(r"x|\+", self._tcl_call(str, "wm", "geometry", self.wm_path))[2:],
                )
            ),
        )

    @position.setter  # type: ignore
    @update_after
    def position(
        self,
        position: int
        | tuple[int, int]
        | list[int]
        | Literal["center", "top-left", "top-right", "bottom-left", "bottom-right"],
    ) -> None:
        if position in _window_pos:
            if position == "center":
                x = int(
                    (self._tcl_call(int, "winfo", "screenwidth", self.wm_path) / 2)
                    - (self.width / 2)
                )
                y = int(
                    (self._tcl_call(int, "winfo", "screenheight", self.wm_path) / 2)
                    - (self.height / 2)
                )
            elif position == "top-left":
                x = y = 0
            elif position == "top-right":
                x = int(self._tcl_call(int, "winfo", "screenwidth", self.wm_path) - self.width)
                y = 0
            elif position == "bottom-left":
                x = 0
                y = int(self._tcl_call(int, "winfo", "screenheight", self.wm_path) - self.height)
            elif position == "bottom-right":
                x = int(self._tcl_call(int, "winfo", "screenwidth", self.wm_path) - self.width)
                y = int(self._tcl_call(int, "winfo", "screenheight", self.wm_path) - self.height)
        elif isinstance(position, (tuple, list)) and len(position) > 1:
            x, y = position
        elif isinstance(position, int):
            x = y = position
        else:
            raise RuntimeError
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"+{x}+{y}")

    @property  # type: ignore
    def bbox(self) -> tuple[int, int, int, int]:
        # TODO: bottom border hack

        window_border_width = self.x - self.position[0]
        title_bar_height = self.root_y - self.position[1]

        x1 = self.position[0]
        y1 = self.root_y - title_bar_height
        x2 = self.root_x + self.width + window_border_width
        y2 = self.y + self.height

        return (x1, y1, x2, y2)

    @property  # type: ignore
    @update_before
    def x(self) -> int:
        return self._tcl_call(int, "winfo", "x", self.wm_path)

    @x.setter  # type: ignore
    @update_after
    def x(self, x: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{x}x{self.y}")

    @property  # type: ignore
    @update_before
    def y(self) -> int:
        return self._tcl_call(int, "winfo", "y", self.wm_path)

    @y.setter  # type: ignore
    @update_after
    def y(self, y: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{self.x}x{y}")

    @property  # type: ignore
    @update_before
    def root_x(self) -> int:
        return self._tcl_call(int, "winfo", "rootx", self.wm_path)

    @property  # type: ignore
    @update_before
    def root_y(self) -> int:
        return self._tcl_call(int, "winfo", "rooty", self.wm_path)

    @property  # type: ignore
    @update_before
    def width(self) -> int:
        return self._tcl_call(int, "winfo", "width", self.wm_path)

    @width.setter  # type: ignore
    @update_after
    def width(self, width: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{width}x{self.height}")

    @property  # type: ignore
    @update_before
    def height(self) -> int:
        return self._tcl_call(int, "winfo", "height", self.wm_path)

    @height.setter  # type: ignore
    @update_after
    def height(self, height: int) -> None:
        self._tcl_call(None, "wm", "geometry", self.wm_path, f"{self.width}x{height}")

    @property  # type: ignore
    @update_before
    def minsize(self) -> tuple[int, int]:
        return self._tcl_call((int), "wm", "minsize", self.wm_path)

    @minsize.setter  # type: ignore
    @update_after
    def minsize(self, size: int | tuple[int, int] | list[int]) -> None:
        if isinstance(size, int):
            width = height = size
        elif isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        else:
            raise RuntimeError
        self._tcl_call(None, "wm", "minsize", self.wm_path, width, height)

    @property  # type: ignore
    @update_before
    def maxsize(self) -> tuple[int, int]:
        return self._tcl_call((int), "wm", "maxsize", self.wm_path)

    @maxsize.setter  # type: ignore
    @update_after
    def maxsize(self, size: int | tuple[int, int] | list[int]) -> None:
        if isinstance(size, int):
            width = height = size
        elif isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        else:
            raise RuntimeError
        self._tcl_call(None, "wm", "maxsize", self.wm_path, width, height)

    @property
    def title(self) -> str:
        return self._tcl_call(None, "wm", "title", self.wm_path, None)

    @title.setter
    def title(self, new_title: str = None) -> None:
        self._tcl_call(None, "wm", "title", self.wm_path, new_title)

    @property
    def topmost(self) -> bool:
        return self._tcl_call(bool, "wm", "attributes", self.wm_path, "-topmost")

    @topmost.setter
    def topmost(self, istopmost: bool = False) -> None:
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-topmost", istopmost)

    @property
    def transparency(self) -> float:
        return self._tcl_call(float, "wm", "attributes", self.wm_path, "-alpha")

    @transparency.setter
    def transparency(self, alpha: float = 1) -> None:
        self._tcl_call(None, "tkwait", "visibility", self.wm_path)
        self._tcl_call(None, "wm", "attributes", self.wm_path, "-alpha", alpha)

    @property
    def resizable(self) -> str:
        return self._resizable

    @resizable.setter
    def resizable(self, direction: Literal["none", "horizontal", "vertical", "both"]):
        resize_dict = {
            "none": (False, False),
            "horizontal": (True, False),
            "vertical": (False, True),
            "both": (True, True),
        }
        try:
            width, height = resize_dict[direction]
        except KeyError:
            raise TclError(
                f"invalid resizable value: {direction!r}. Allowed values: 'none',"
                + " 'horizontal' 'vertical', 'both'"
            )
        self._resizable = direction
        self._tcl_call(None, "wm", "resizable", self.wm_path, width, height)

    @property
    def user_last_active(self) -> int:
        return self._tcl_call(int, "tk", "inactive") / 1000

    @property
    def scaling(self) -> int:
        return self._tcl_call(int, "tk", "scaling", "-displayof", self.wm_path)

    @scaling.setter
    def scaling(self, factor: int) -> None:
        self._tcl_call(None, "tk", "scaling", "-displayof", self.wm_path, factor)

    def _get_theme_aliases(self) -> dict[str, str]:
        # available_themes property should use this
        theme_dict = {"clam": "clam", "legacy": "default", "native": "clam"}

        wm = Platform.windowing_system

        if wm == "win32":
            theme_dict["native"] = "vista"
        elif wm == "aqua":
            theme_dict["native"] = "aqua"

        return theme_dict

    @property
    def theme(self) -> str:
        theme_dict = {"clam": "clam", "default": "legacy"}

        wm = Platform.windowing_system

        if wm == "win32":
            theme_dict["vista"] = "native"
        elif wm == "aqua":
            theme_dict["aqua"] = "native"

        result = self._tcl_call(str, "ttk::style", "theme", "use")
        return theme_dict[result]

    @theme.setter
    def theme(self, theme) -> None:
        self._tcl_call(None, "ttk::style", "theme", "use", self._get_theme_aliases()[theme])
