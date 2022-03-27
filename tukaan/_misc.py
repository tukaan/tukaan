from __future__ import annotations

import collections
from abc import ABC, abstractstaticmethod
from fractions import Fraction
from typing import Callable, Tuple, cast

from PIL import ImageGrab  # type: ignore

from ._info import System
from ._tcl import Tcl
from ._utils import ClassPropertyMetaClass, classproperty, reversed_dict
from .exceptions import TclError

intround: Callable[[float], int] = lambda x: int(round(x, 0))
round4: Callable[[float], float] = lambda x: round(x, 4)


Bbox = collections.namedtuple("Bbox", ["x", "y", "width", "height"])


class Clipboard(metaclass=ClassPropertyMetaClass):
    @classmethod
    def __repr__(cls) -> str:
        return f"{type(cls).__name__}(content={cls.get()})"

    @classmethod
    def clear(cls) -> None:
        Tcl.call(None, "clipboard", "clear")

    @classmethod
    def append(cls, content) -> None:
        Tcl.call(None, "clipboard", "append", content)

    def __add__(self, content) -> Clipboard:
        self.append(content)
        return self

    @classmethod
    def get(cls) -> str | None:
        try:
            return Tcl.call(str, "clipboard", "get")
        except TclError:
            try:
                return ImageGrab.grabclipboard()
            except NotImplementedError:
                # grabclipboard() is macOS and Windows only
                return None

    @classmethod
    def set(cls, new_content: str) -> None:
        Tcl.call(None, "clipboard", "clear")
        Tcl.call(None, "clipboard", "append", new_content)

    @classproperty
    def content(cls) -> str:
        return cls.get()

    @content.setter
    def content(cls, new_content: str) -> None:
        cls.set(new_content)


class Cursor(collections.namedtuple("Cursor", "cursor"), metaclass=ClassPropertyMetaClass):
    _cursor_dict: dict[str | None, str] = {
        "crosshair": "crosshair",
        "default": "arrow",
        "e-resize": "right_side",
        "help": "question_arrow",
        "move": "fleur",
        "n-resize": "top_side",
        "ne-sw-resize": "top_right_corner",
        "not-allowed": "circle",
        "ns-resize": "sb_v_double_arrow",
        "nw-se-resize": "top_left_corner",
        "pointer": "hand2",
        "progress": "arrow",  # for cross-platform compatibility
        "s-resize": "bottom_side",
        "text": "xterm",
        "w-resize": "left_side",
        "wait": "watch",
        "we-resize": "sb_h_double_arrow",
        None: "none",
    }

    _win_cursor_dict: dict[str | None, str] = {
        "not-allowed": "no",
        "progress": "starting",
        "ne-sw-resize": "size_ne_sw",
        "ns-resize": "size_ns",
        "nw-se-resize": "size_nw_se",
        "wait": "wait",
        "we-resize": "size_we",
    }

    if System.os == "Windows":
        _cursor_dict = {**_cursor_dict, **_win_cursor_dict}

    def __to_tcl__(self) -> str:
        return self._cursor_dict[self.cursor]

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> Cursor:
        return cls(reversed_dict(cls._cursor_dict)[tcl_value])

    @classproperty
    def x(cls) -> int:
        return Tcl.call(int, "winfo", "pointerx", ".")

    @x.setter
    @Tcl.update_after
    def x(cls, new_x: int) -> None:
        Tcl.call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-x",
            new_x,
            "-y",
            cls.y,
        )

    @classproperty
    def y(cls) -> int:
        return Tcl.call(int, "winfo", "pointery", ".")

    @y.setter
    @Tcl.update_after
    def y(cls, new_y: int) -> None:
        Tcl.call(
            None,
            "event",
            "generate",
            ".",
            "<Motion>",
            "-warp",
            "1",
            "-y",
            new_y,
            "-x",
            cls.x,
        )

    @classproperty
    def position(cls) -> tuple[int, int]:
        return (cls.x, cls.y)

    @position.setter
    @Tcl.update_after
    def position(cls, new_pos: int | tuple[int, int] | list[int]) -> None:
        if isinstance(new_pos, (tuple, list)) and len(new_pos) > 1:
            x, y = new_pos
        elif isinstance(new_pos, int):
            x = y = new_pos
        else:
            raise RuntimeError

        Tcl.call(None, "event", "generate", ".", "<Motion>", "-warp", "1", "-x", x, "-y", y)
