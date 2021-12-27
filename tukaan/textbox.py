from __future__ import annotations

import warnings
from collections import abc, namedtuple
from functools import partialmethod
from pathlib import Path
from typing import Any, Iterator, Optional

from PIL import Image

from ._base import BaseWidget, CgetAndConfigure, TkWidget
from ._constants import _wraps
from ._images import Icon
from ._misc import Color, Font, ScreenDistance
from ._utils import (
    ClassPropertyMetaClass,
    _images,
    _text_tags,
    classproperty,
    counts,
    py_to_tcl_arguments,
    update_before,
)
from .exceptions import TclError
from .scrollbar import Scrollbar
from ._variables import Integer


class Tag(CgetAndConfigure, metaclass=ClassPropertyMetaClass):
    _widget: TextBox
    _keys = {
        "bg_color": (Color, "background"),
        "color": (Color, "foreground"),
        "first_line_margin": (ScreenDistance, "lmargin1"),
        "font": Font,
        "hanging_line_margin": (ScreenDistance, "lmargin2"),
        "hidden": (bool, "elide"),
        "justify": str,
        "offset": ScreenDistance,
        "right_margin": (ScreenDistance, "rmargin"),
        "space_after_paragraph": (ScreenDistance, "spacing3"),
        "space_before_paragraph": (ScreenDistance, "spacing1"),
        "space_before_wrapped_line": (ScreenDistance, "spacing2"),
        "strikethrough": (bool, "overstrike"),
        "tab_stops": (str, "tabs"),
        "underline": bool,
        "wrap": _wraps,
    }

    def __init__(
        self,
        _name: str = None,
        *,
        bg_color=None,
        bold=False,
        first_line_margin=None,
        font=None,
        color=None,
        hanging_line_margin=None,
        hidden: Optional[bool] = None,
        italic=False,
        justify=None,
        offset=None,
        right_margin=None,
        space_after_paragraph=None,
        space_before_paragraph=None,
        space_before_wrapped_line=None,
        strikethrough: bool = False,
        tab_stops=None,
        underline: bool = False,
        wrap=None,
    ) -> None:
        self._name = _name or f"{self._widget.tcl_path}:tag_{next(counts['textbox_tag'])}"
        _text_tags[self._name] = self

        self._tcl_call(
            None,
            self,
            "configure",
            background=bg_color,
            elide=hidden,
            font=font,
            foreground=color,
            justify=justify,
            lmargin1=first_line_margin,
            lmargin2=hanging_line_margin,
            offset=offset,
            rmargin=right_margin,
            spacing1=space_before_paragraph,
            spacing2=space_before_wrapped_line,
            spacing3=space_after_paragraph,
            tabs=tab_stops,
            wrap=_wraps[wrap],
        )

    def __repr__(self) -> str:
        return f"<tukaan.TextBox.Tag named {self._name!r}>"

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._keys.keys():
            self.config(**{key: value})
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key: str) -> Any:
        if key in self._keys.keys():
            return self._cget(key)
        else:
            return super().__getattribute__(key)

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value: str) -> Tag:
        return _text_tags[value]

    def _tcl_call(self, returntype: Any, _dumb_self, subcommand: str, *args, **kwargs) -> Any:
        return self._widget._tcl_call(
            returntype,
            self._widget,
            "tag",
            subcommand,
            self._name,
            *args,
            *py_to_tcl_arguments(**kwargs),
        )

    def add(self, start: TextIndex = None, end: TextIndex = None) -> None:
        start = self._widget.start if start is None else start
        end = self._widget.end if end is None else end

        self._tcl_call(None, self, "add", start, end)

    def delete(self) -> None:
        self._tcl_call(None, self, "delete")

    def remove(self, start: TextIndex = None, end: TextIndex = None) -> None:
        start = self._widget.start if start is None else start
        end = self._widget.end if end is None else end

        self._tcl_call(None, self, "remove", start, end)

    @property
    def ranges(self):
        result = self._tcl_call((self._widget.index,), self, "ranges")

        for start, end in zip(result[0::2], result[1::2]):
            yield self._widget.range(start, end)

    def _prev_next_range(
        self, direction: str, start: TextIndex, end: Optional[TextIndex] = None
    ) -> None | TextRange:
        if end is None:
            end = {"prev": self._widget.start, "next": self._widget.end}[direction]

        result = self._tcl_call((self._widget.index,), self, f"{direction}range", start, end)

        if not result:
            return None

        return self._widget.range(*result)

    prev_range = partialmethod(_prev_next_range, "prev")
    next_range = partialmethod(_prev_next_range, "next")

    @classproperty
    def hidden(cls) -> Tag:
        return cls(_name="hidden", hidden=True)


class TextRange(namedtuple("TextRange", "start end")):
    def get(self):
        return self._widget.get(self)

    def __contains__(self, x):
        return self.start <= x <= self.end


class TextIndex(namedtuple("TextIndex", "line column")):
    _widget: TextBox

    def __new__(
        cls,
        *args,
        x: int | None = None,
        y: int | None = None,
    ) -> TextIndex:
        result = None

        if len(args) == 2:
            # line and column numbers
            line, column = args
        elif isinstance(args[0], (str, Icon, Image.Image, TkWidget)):
            # string from from_tcl() OR mark name, image name or widget name
            result = cls._widget._tcl_call(str, cls._widget.tcl_path, "index", args[0])
        elif isinstance(x, (int, float, ScreenDistance)) and isinstance(
            y, (int, float, ScreenDistance)
        ):
            # x and y
            result = cls._widget._tcl_call(str, cls._widget.tcl_path, "index", f"@{x},{y}")

        if result:
            line, column = tuple(map(int, result.split(".")))

        return super(TextIndex, cls).__new__(cls, line, column)  # type: ignore

    def to_tcl(self) -> str:
        return f"{self.line}.{self.column}"

    @classmethod
    def from_tcl(cls, string: str) -> TextIndex:
        return cls(string)

    def _compare(self, first: TextIndex, second: TextIndex, operator: str) -> bool:
        return self._widget._tcl_call(bool, self._widget, "compare", first, operator, second)

    def __eq__(self, other: TextIndex) -> bool:  # type: ignore[override]
        if not isinstance(other, TextIndex):
            return NotImplemented
        return self._compare(self, other, "==")

    def __lt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(self, other, "<")

    def __gt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(self, other, ">")

    def __le__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(self, other, "<=")

    def __ge__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(self, other, ">=")

    @property
    def between_start_end(self) -> TextIndex:
        if self < self._widget.start:
            return self._widget.start
        if self > self._widget.end:
            return self._widget.end
        return self

    def forward(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self.from_tcl(
            f"{self.to_tcl()} + {lines} lines + {chars} chars + {indices} indices"
        ).between_start_end

    def back(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self.from_tcl(
            f"{self.to_tcl()} - {lines} lines - {chars} chars - {indices} indices"
        ).between_start_end

    def _apply_suffix(self, suffix) -> TextIndex:
        return self.from_tcl(f"{self.to_tcl()} {suffix}").between_start_end

    @property
    def linestart(self) -> TextIndex:
        return self._apply_suffix("linestart")

    @property
    def lineend(self) -> TextIndex:
        return self._apply_suffix("lineend")

    @property
    def wordstart(self) -> TextIndex:
        return self._apply_suffix("wordstart")

    @property
    def wordend(self) -> TextIndex:
        return self._apply_suffix("wordend")


class Marks(abc.MutableMapping):
    _widget: TextBox

    def __get_names(self) -> list[str]:
        return self._widget._tcl_call([str], self._widget.tcl_path, "mark", "names")

    def __iter__(self) -> Iterator:
        return iter(self.__get_names())

    def __len__(self) -> int:
        return len(self.__get_names())

    def __contains__(self, mark: object) -> bool:
        return mark in self.__get_names()

    def __setitem__(self, name: str, index: TextIndex) -> None:
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "set", name, index)

    def __getitem__(self, name: str) -> TextIndex:
        if name not in self:
            raise KeyError(f"Mark {name!r} doesn't exists in {self._widget}")

        return self._widget.index(name)

    def __delitem__(self, name: str) -> None:
        if name == "insert":
            raise TclError("can't delete insertion cursor")
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "unset", name)


class TextHistory:
    _widget: TextBox

    def call_subcommand(self, *args):
        if self._widget.track_history is False:
            warnings.warn(
                "undoing is disabled on this textbox widget. Use `track_history=True` to enable it.",
                stacklevel=3,
            )
        return self._widget._tcl_call(bool, self._widget, "edit", *args)

    @property
    def can_redo(self):
        return self.call_subcommand("canredo")

    @property
    def can_undo(self):
        return self.call_subcommand("canundo")

    def redo(self, number=1):
        try:
            for i in range(number):
                self.call_subcommand("redo")
        except TclError:
            return

    def undo(self, number=1):
        try:
            for i in range(number):
                self.call_subcommand("undo")
        except TclError:
            return

    def clear(self):
        self.call_subcommand("reset")

    def add_sep(self):
        self.call_subcommand("separator")

    @property
    def limit(self) -> int:
        return self._widget._tcl_call(int, self._widget, "cget", "-maxundo")

    @limit.setter
    def limit(self, new_limit: int) -> None:
        self._widget._tcl_call(None, self._widget, "configure", "-maxundo", new_limit)


class _textbox_frame(BaseWidget):
    _tcl_class = "ttk::frame"
    _keys: dict[str, Any | tuple[Any, str]] = {}

    def __init__(self, parent) -> None:
        BaseWidget.__init__(self, parent)


class TextBox(BaseWidget):
    _tcl_class = "text"
    _keys = {
        "font": Font,
        "on_xscroll": ("func", "xscrollcommand"),
        "on_yscroll": ("func", "yscrollcommand"),
        "track_history": (bool, "undo"),
        "wrap": _wraps,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        font=("monospace", 10),
        overflow: tuple[bool | str, bool | str] = ("auto", "auto"),
        track_history=False,
        wrap=None,
    ) -> None:
        assert wrap in _wraps, f"wrapping must be one of {tuple(_wraps.keys())}"
        wrap = _wraps[wrap]

        self._frame = _textbox_frame(parent)

        BaseWidget.__init__(
            self,
            self._frame,
            autoseparators=True,
            font=font,
            highlightthickness=0,
            relief="flat",
            undo=track_history,
            wrap=wrap,
        )
        self._tcl_eval(
            None,
            f"grid rowconfigure {self._frame.tcl_path} 0 -weight 1 \n"
            + f"grid columnconfigure {self._frame.tcl_path} 0 -weight 1 \n"
            + f"grid {self.tcl_path} -row 0 -column 0 -sticky nsew",
        )

        if overflow is not None:
            self.overflow = overflow

        self.index = TextIndex
        self.range = TextRange
        self.Tag = Tag
        self.marks = Marks()
        self.history = TextHistory()
        for attr in (self.index, self.range, self.Tag, self.marks, self.history):
            setattr(attr, "_widget", self)

        self.layout = self._frame.layout

    def _make_hor_scroll(self, hide=True):
        self._h_scroll = Scrollbar(self._frame, orientation="horizontal", auto_hide=hide)
        self._h_scroll.attach(self)
        self._h_scroll.layout.grid(row=1, hor_align="stretch")

    def _make_vert_scroll(self, hide=True):
        self._v_scroll = Scrollbar(self._frame, orientation="vertical", auto_hide=hide)
        self._v_scroll.attach(self)
        self._v_scroll.layout.grid(col=1, vert_align="stretch")

    @property
    def start(self) -> TextIndex:
        return self.index(1, 0)

    @property
    def end(self) -> TextIndex:
        return self._tcl_call(self.index, self, "index", "end - 1 char")

    def insert(self, index: TextIndex, content: str, **kwargs) -> None:
        if isinstance(content, (Image.Image, Icon)):
            margin = kwargs.pop("margin", None)
            padx = pady = None
            if margin:
                if isinstance(margin, int) or len(margin) == 1:
                    padx = pady = margin
                elif len(margin) == 2:
                    padx, pady = margin
                else:
                    raise ValueError(
                        "unfortunately 4 side margins aren't supported for embedded images"
                    )

            align = kwargs.pop("align", None)

            # fmt: off
            to_call = ("image", "create", index, *py_to_tcl_arguments(image=content, padx=padx, pady=pady, align=align))
            # fmt: on
        elif isinstance(content, TkWidget):
            margin = kwargs.pop("margin", None)
            padx = pady = None
            if margin:
                if isinstance(margin, int) or len(margin) == 1:
                    padx = pady = margin
                elif len(margin) == 2:
                    padx, pady = margin
                else:
                    raise ValueError(
                        "unfortunately 4 side margins aren't supported for embedded widgets"
                    )

            align = kwargs.pop("align", None)
            stretch = False
            if align == "stretch":
                stretch = True
                align = None

            # fmt: off
            to_call = ("window", "create", index, *py_to_tcl_arguments(window=content, padx=padx, pady=pady, align=align, stretch=stretch))
            # fmt: on
        elif isinstance(content, Path):
            with open(str(content.resolve())) as file:
                to_call = ("insert", index, file.read())
        else:
            to_call = ("insert", index, content)

        if kwargs:
            raise TypeError(f"insert() got unexpected keyword argument(s): {tuple(kwargs.keys())}")
        self._tcl_call(None, self, *to_call)

    def delete(
        self, start: Optional[TextIndex | TextRange] = None, end: Optional[TextIndex] = None
    ) -> None:
        if isinstance(start, TextRange):
            start, end = start
        else:
            start = self.start if start is None else start
            end = self.end if end is None else end

        self._tcl_call(None, self, "delete", start, end)

    def get(
        self, start: Optional[TextIndex | TextRange] = None, end: Optional[TextIndex] = None
    ) -> str:
        if isinstance(start, TextRange):
            start, end = start
        else:
            start = self.start if start is None else start
            end = self.end if end is None else end

        return self._tcl_call(str, self, "get", start, end)

    def replace(self, *args, tag: Optional[Tag] = None) -> None:
        if isinstance(args[0], TextRange) and isinstance(args[1], str):
            text = args[1]
            start, end = args[0]
        elif (
            len(args) == 3
            and isinstance(args[0], TextIndex)
            and isinstance(args[1], TextIndex)
            and isinstance(args[2], str)
        ):
            text = args[2]
            start = self.start if args[0] is None else args[0]
            end = self.end if args[1] is None else args[1]
        else:
            raise ValueError("invalid arguments. See help(TextBox.replace).")

        self._tcl_call(None, self, "replace", start, end, text, tag)

    def search(
        self,
        pattern,
        start,
        stop="end",
        *,
        backwards=False,
        case_sensitive=True,
        count_hidden=False,
        exact=False,
        forwards=False,
        match_newline=False,
        regex=False,
        strict_limits=False,
        variable=None,
    ):

        if stop == self.end:
            stop = "end - 1 chars"

        if variable is None:
            variable = Integer()

        to_call = []

        if backwards:
            to_call.append("-backwards")
        if not case_sensitive:
            to_call.append("-nocase")
        if count_hidden:
            to_call.append("-elide")
        if exact:
            to_call.append("-exact")
        if forwards:
            to_call.append("-forwards")
        if match_newline:
            to_call.append("-nolinestop")
        if regex:
            to_call.append("-regexp")
        if strict_limits:
            to_call.append("-strictlimits")

        if pattern and pattern[0] == "-":
            to_call.append("--")

        while True:
            result = self._tcl_call(str, self.tcl_path, "search", "-count", variable, *to_call, pattern, start, stop)
            if not result:
                break
            yield self.range(self.index(result), self.index(result).forward(chars=variable.get()))
            start = result + "+ 1 chars"

    def scroll_to(self, index: TextIndex) -> None:
        self._tcl_call(None, self, "see", index)

    def x_scroll(self, subcommand, fraction):
        self._tcl_call(None, self, "xview", subcommand, fraction)

    def y_scroll(self, subcommand, fraction):
        self._tcl_call(None, self, "yview", subcommand, fraction)

    @property
    def overflow(self):
        return self._overflow

    @overflow.setter
    def overflow(self, new_overflow: tuple[str, str]):
        if hasattr(self, "_h_scroll"):
            self._h_scroll.destroy()
        if hasattr(self, "_v_scroll"):
            self._v_scroll.destroy()

        if len(new_overflow) == 1:
            new_overflow = new_overflow * 2

        if new_overflow == (False, False):
            pass
        elif new_overflow == (True, False):
            self._make_hor_scroll(False)
        elif new_overflow == (False, True):
            self._make_vert_scroll(False)
        elif new_overflow == (True, True):
            self._make_hor_scroll(False)
            self._make_vert_scroll(False)
        elif new_overflow == ("auto", False):
            self._make_hor_scroll()
        elif new_overflow == (False, "auto"):
            self._make_vert_scroll()
        elif new_overflow == ("auto", True):
            self._make_hor_scroll()
            self._make_vert_scroll(False)
        elif new_overflow == (True, "auto"):
            self._make_hor_scroll(False)
            self._make_vert_scroll()
        elif new_overflow == ("auto", "auto"):
            self._make_hor_scroll()
            self._make_vert_scroll()
        else:
            raise ValueError(f"invalid overflow value: {new_overflow}")

        self._overflow = new_overflow

    @property
    def text(self):
        return self.get()

    @text.setter
    def text(self, new_text):
        self.delete()
        self.insert(self.end, new_text)

    @property
    def cursor_pos(self):
        return self.marks["insert"]

    @cursor_pos.setter
    def cursor_pos(self, new_pos: TextIndex):
        self.marks["insert"] = new_pos

    @property
    def content(self) -> list[tuple[TextIndex, str | Tag | Icon | Image.Image | TkWidget]]:
        result = []  # type: ignore
        unclosed_tags = {}

        def add_item(type, value, index):
            nonlocal result
            nonlocal unclosed_tags

            if type == "tagon":
                unclosed_tags[value] = (index, len(result))
                return
            elif type == "tagoff":
                if value in unclosed_tags:
                    result.insert(
                        unclosed_tags[value][1],
                        (
                            self.range(self.index(unclosed_tags[value][0]), self.index(index)),
                            Tag.from_tcl(value),
                        ),
                    )
                    return

            convert = {
                "image": lambda x: _images[x],
                "mark": lambda x: f"TextBox.marks[{x!r}]",
                "text": str,
                "window": TkWidget.from_tcl,
            }[type]

            result.append((self.index(index), convert(value)))

        self._tcl_call(str, self, "dump", "-all", "-command", add_item, "1.0", "end - 1 chars")
        return result

    @update_before
    def line_info(self, index: TextIndex) -> dict[str, ScreenDistance]:
        """Returns the accurate height only if the TextBox widget has already laid out"""
        keys = ("x_1", "y_1", "x_2", "y_2", "baseline")
        result = self._tcl_call(
            (ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance),
            self,
            "dlineinfo",
            index,
        )

        return {key: value for key, value in zip(keys, result)}

    def count(
        self, start: Optional[TextIndex | TextRange] = None, end: Optional[TextIndex] = None
    ) -> dict[str, int | ScreenDistance]:
        if isinstance(start, TextRange):
            start, end = start
        else:
            start = self.start if start is None else start
            end = self.end if end is None else end

        keys = (
            "chars",
            "displayed_chars",
            "displayed_indices",
            "displayed_lines",
            "indices",
            "lines",
            "width",
            "height",
        )
        result = self._tcl_call(
            (int, int, int, int, int, int, ScreenDistance, ScreenDistance),
            self,
            "count",
            "-chars",
            "-displaychars",
            "-displayindices",
            "-displaylines",
            "-indices",
            "-lines",
            "-xpixels",
            "-ypixels",
            start,
            end,
        )

        return {key: value for key, value in zip(keys, result)}
