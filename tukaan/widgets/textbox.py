from __future__ import annotations

import warnings
from collections import abc, namedtuple
from functools import partialmethod
from pathlib import Path
from typing import Any, Iterator

import _tkinter as tk
from PIL import Image  # type: ignore

from tukaan._enums import CaretStyle, InactiveCaretStyle, Wrap
from tukaan._images import Icon
from tukaan._tcl import Tcl
from tukaan._utils import _images, _text_tags, counts, seq_pairs
from tukaan._variables import Integer
from tukaan.colors import Color
from tukaan.data import TabStop
from tukaan.exceptions import TclError
from tukaan.fonts import Font
from tukaan.screen_distance import ScreenDistance

from ._base import (
    BaseWidget,
    GetSetAttrMixin,
    InputControlWidget,
    OutputDisplayWidget,
    TkWidget,
    XScrollable,
    YScrollable,
)
from .frame import Frame
from .scrollbar import ScrollBar


class _TabStopsProperty:
    @property
    def tab_stops(self) -> list[TabStop]:
        result = []
        for pos, align in seq_pairs(self._get([str], "tabs")):
            result.append(TabStop(pos, align))
        return result

    @tab_stops.setter
    def tab_stops(self, tab_stops: TabStop | list[TabStop]) -> None:
        if tab_stops is None:
            return

        if not isinstance(tab_stops, (list, tuple)):
            tab_stops = (tab_stops,)

        self._set(tabs=[y for x in tab_stops for y in x.__to_tcl__()])


class Tag(GetSetAttrMixin, _TabStopsProperty):
    _widget: TextBox
    _keys = {
        "bg_color": (Color, "background"),
        "fg_color": (Color, "foreground"),
        "first_line_margin": (ScreenDistance, "lmargin1"),
        "font": Font,
        "hanging_line_margin": (ScreenDistance, "lmargin2"),
        "hidden": (bool, "elide"),
        "justify": str,
        "offset": ScreenDistance,
        "right_margin": (ScreenDistance, "rmargin"),
        "right_margin_bg": (ScreenDistance, "rmargincolor"),
        "selection_bg": (Color, "selectbackground"),
        "selection_fg": (Color, "selectforeground"),
        "space_after_paragraph": (ScreenDistance, "spacing3"),
        "space_before_paragraph": (ScreenDistance, "spacing1"),
        "space_before_wrapped_line": (ScreenDistance, "spacing2"),
        "strikethrough_color": (Color, "overstrikefg"),
        "tab_style": (str, "tabstyle"),
        "underline_color": (Color, "underlinefg"),
        "wrap": Wrap,
    }

    def __init__(
        self,
        _name: str = None,
        *,
        bg_color: Color | None = None,
        fg_color: Color | None = None,
        first_line_margin: int | ScreenDistance | None = None,
        font: Font | tuple[str | int | bool] | None = None,
        hanging_line_margin: int | ScreenDistance | None = None,
        hidden: bool | None = None,
        justify: str | None = None,
        offset: int | ScreenDistance | None = None,
        right_margin: int | ScreenDistance | None = None,
        right_margin_bg: Color | None = None,
        selection_bg: Color | None = None,
        selection_fg: Color | None = None,
        space_after_paragraph: int | ScreenDistance | None = None,
        space_before_paragraph: int | ScreenDistance | None = None,
        space_before_wrapped_line: int | ScreenDistance | None = None,
        strikethrough_color: Color | None = None,
        tab_stops: TabStop | list[TabStop] | tuple[TabStop] | None = None,
        tab_style: str | None = None,
        underline_color: Color | None = None,
        wrap: Wrap | None = None,
    ) -> None:
        self._name = _name or f"{self._widget._name}:tag_{next(counts['textbox_tag'])}"
        _text_tags[self._name] = self

        self._call_tag_subcmd(
            None,
            "configure",
            background=bg_color,
            elide=hidden,
            font=font,
            foreground=fg_color,
            justify=justify,
            lmargin1=first_line_margin,
            lmargin2=hanging_line_margin,
            offset=offset,
            overstrikefg=strikethrough_color,
            rmargin=right_margin,
            rmargincolor=right_margin_bg,
            selectbackground=selection_bg,
            selectforeground=selection_fg,
            spacing1=space_before_paragraph,
            spacing2=space_before_wrapped_line,
            spacing3=space_after_paragraph,
            tabstyle=tab_style,
            underlinefg=underline_color,
            wrap=wrap,
        )
        self.tab_stops = tab_stops

    def __repr__(self) -> str:
        return f"<tukaan.TextBox.Tag named {self._name!r}>"

    def __to_tcl__(self):
        return self._name

    @classmethod
    def __from_tcl__(cls, value: str) -> Tag:
        return _text_tags[value]

    def _call_tag_subcmd(self, returntype: Any, subcommand: str, *args, **kwargs) -> Any:
        return Tcl.call(
            returntype,
            self._widget,
            "tag",
            subcommand,
            self._name,
            *args,
            *Tcl.to_tcl_args(**kwargs),
        )

    def _get(self, type_spec, key):
        return self._call_tag_subcmd(type_spec, "cget", f"-{key}")

    def _set(self, **kwargs):
        self._call_tag_subcmd(None, "configure", *Tcl.to_tcl_args(**kwargs))

    def add(self, *indexes) -> None:
        self._call_tag_subcmd(None, "add", *self._widget._convert_indices_or_range_to_tcl(indexes))

    def delete(self) -> None:
        self._call_tag_subcmd(None, "delete")

    def remove(self, *indexes) -> None:
        self._call_tag_subcmd(
            None, "remove", *self._widget._convert_indices_or_range_to_tcl(indexes)
        )

    @property
    def ranges(self):
        result = self._call_tag_subcmd((self._widget.index,), "ranges")

        for start, end in zip(result[0::2], result[1::2]):
            yield self._widget.range(start, end)

    def _prev_next_range(
        self, direction: str, start: TextIndex, end: TextIndex | None = None
    ) -> None | TextRange:
        if end is None:
            end = {"prev": self._widget.start, "next": self._widget.end}[direction]

        result = self._call_tag_subcmd((self._widget.index,), f"{direction}range", start, end)

        if not result:
            return None

        return self._widget.range(*result)

    prev_range = partialmethod(_prev_next_range, "prev")
    next_range = partialmethod(_prev_next_range, "next")


class TextIndex(namedtuple("TextIndex", ["line", "column"])):
    _widget: TextBox
    __slots__ = ()

    def __new__(cls, *index, no_check=False) -> TextIndex:
        result = None

        if isinstance(index, tuple) and len(index) == 2:
            # line and column numbers
            line, col = index
        else:
            index = index[0]
            if isinstance(index, int):
                if index in {0, 1}:
                    line, col = 1, 0
                elif index == -1:
                    result = Tcl.call(str, cls._widget._name, "index", "end - 1 chars")
            elif isinstance(index, (str, Icon, Image.Image, TkWidget, tk.Tcl_Obj)):
                # index string Tcl._from() OR mark name, image name or widget name
                result = Tcl.call(str, cls._widget._name, "index", index)
            elif isinstance(index, tuple):
                line, col = index
            else:
                raise TypeError

        if result:
            line, col = tuple(map(int, result.split(".")))

        if not no_check:
            if (line, col) < tuple(cls._widget.start):
                return cls._widget.start
            if (line, col) > tuple(cls._widget.end):
                return cls._widget.end

        return super().__new__(cls, line, col)  # type: ignore

    def __to_tcl__(self) -> str:
        return f"{self.line}.{self.column}"

    @classmethod
    def __from_tcl__(cls, string: str) -> TextIndex:
        return cls(string)

    def _compare(self, other: TextIndex, operator: str) -> bool:
        return Tcl.call(bool, self._widget, "compare", self, operator, other)

    def __eq__(self, other: TextIndex) -> bool:  # type: ignore[override]
        if not isinstance(other, TextIndex):
            return NotImplemented
        return self._compare(other, "==")

    def __lt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, "<")

    def __gt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, ">")

    def __le__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, "<=")

    def __ge__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, ">=")

    def __add__(self, arg: int | TextIndex) -> TextIndex:  # type: ignore[override]
        if isinstance(arg, TextIndex):
            return TextIndex(self.line + arg.line, self.column + arg.column)
        return self.forward(indices=arg)

    def __sub__(self, arg: int | TextIndex) -> TextIndex:  # type: ignore[override]
        if isinstance(arg, TextIndex):
            return TextIndex(self.line - arg.line, self.column - arg.column)
        return self.back(indices=arg)

    def clamp(self) -> TextIndex:
        if self < self._widget.start:
            return self._widget.start
        if self > self._widget.end:
            return self._widget.end
        return self

    def _move(self, dir_, chars, indices, lines):
        move_str = ""
        if chars:
            move_str += f" {dir_} {chars} chars"
        if indices:
            move_str += f" {dir_} {indices} indices"
        if lines:
            move_str += f" {dir_} {lines} lines"

        return self.__from_tcl__(self.__to_tcl__() + move_str).clamp()

    def forward(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self._move("+", chars, indices, lines)

    def back(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self._move("-", chars, indices, lines)

    def _apply_suffix(self, suffix) -> TextIndex:
        return self.__from_tcl__(f"{self.__to_tcl__()} {suffix}").clamp()

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


class TextRange(namedtuple("TextRange", ["start", "end"])):
    _widget: TextBox

    def __new__(
        cls, *indexes: slice | tuple[tuple[int, int], tuple[int, int]] | tuple[TextIndex, TextIndex]
    ) -> TextRange:
        if isinstance(indexes[0], slice):
            start, stop = indexes[0].start, indexes[0].stop
        else:
            start, stop = indexes

        if isinstance(start, tuple):
            start = cls._widget.index(*start)

        if isinstance(stop, tuple):
            stop = cls._widget.index(*stop)

        if start is None:
            start = cls._widget.start

        if stop is None:
            stop = cls._widget.end

        return super().__new__(cls, start, stop)  # type: ignore

    def get(self):
        return self._widget.get(self)

    def __contains__(self, index: TextIndex):  # type: ignore[override]
        return self.start <= index < self.end


class TextMarks(abc.MutableMapping):
    _widget: TextBox
    __slots__ = "_widget"

    def __get_names(self) -> list[str]:
        return Tcl.call([str], self._widget._name, "mark", "names")

    def __iter__(self) -> Iterator:
        return iter(self.__get_names())

    def __len__(self) -> int:
        return len(self.__get_names())

    def __contains__(self, mark: object) -> bool:
        return mark in self.__get_names()

    def __setitem__(self, name: str, index: TextIndex) -> None:
        Tcl.call(None, self._widget._name, "mark", "set", name, index)

    def __getitem__(self, name: str) -> TextIndex | None:
        if name not in self.__get_names():
            return None

        return self._widget.index(name)

    def __delitem__(self, name: str) -> None:
        if name == "insert":
            raise RuntimeError("can't delete caret")
        Tcl.call(None, self._widget._name, "mark", "unset", name)


class TextHistory:
    _widget: TextBox
    __slots__ = "_widget"

    def call_subcommand(self, *args) -> bool:
        if not self._widget.track_history:
            warnings.warn(
                "undoing is disabled on this textbox widget. Use `track_history=True` to enable it.",
                stacklevel=3,
            )
        return Tcl.call(bool, self._widget, "edit", *args)

    @property
    def can_redo(self) -> bool:
        return self.call_subcommand("canredo")

    @property
    def can_undo(self) -> bool:
        return self.call_subcommand("canundo")

    def redo(self, number=1) -> None:
        try:
            for i in range(number):
                self.call_subcommand("redo")
        except TclError:
            return

    __rshift__ = redo

    def undo(self, number=1) -> None:
        try:
            for i in range(number):
                self.call_subcommand("undo")
        except TclError:
            return

    __lshift__ = undo

    def clear(self) -> None:
        self.call_subcommand("reset")

    def add_sep(self) -> None:
        self.call_subcommand("separator")

    @property
    def limit(self) -> int:
        return Tcl.call(int, self._widget, "cget", "-maxundo")

    @limit.setter
    def limit(self, new_limit: int) -> None:
        Tcl.call(None, self._widget, "configure", "-maxundo", new_limit)


LineInfo = namedtuple("LineInfo", ["x", "y", "width", "height", "baseline"])
RangeInfo = namedtuple(
    "RangeInfo",
    [
        "chars",
        "displayed_chars",
        "displayed_indices",
        "displayed_lines",
        "indices",
        "lines",
        "width",
        "height",
    ],
)


class TextBox(
    BaseWidget, _TabStopsProperty, InputControlWidget, OutputDisplayWidget, XScrollable, YScrollable
):
    index: type[TextIndex]
    range: type[TextRange]
    Tag: type[Tag]
    marks: TextMarks
    history: TextHistory

    _tcl_class = "text"
    _keys = {
        "bg_color": (Color, "background"),
        "caret_color": (Color, "insertbackground"),
        "caret_offtime": (int, "insertofftime"),
        "caret_ontime": (int, "insertontime"),
        "caret_style": (CaretStyle, "blockcursor"),
        "caret_width": (ScreenDistance, "insertwidth"),
        "fg_color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "font": Font,
        "height": ScreenDistance,
        "inactive_caret_style": (InactiveCaretStyle, "insertunfocussed"),
        "inactive_selection_bg": (Color, "inactiveselectbackground"),
        "on_xscroll": ("func", "xscrollcommand"),
        "on_yscroll": ("func", "yscrollcommand"),
        "resize_along_chars": (bool, "setgrid"),
        "selection_bg": (Color, "selectbackground"),
        "selection_fg": (Color, "selectforeground"),
        "space_after_paragraph": (ScreenDistance, "spacing3"),
        "space_before_paragraph": (ScreenDistance, "spacing1"),
        "space_before_wrapped_line": (ScreenDistance, "spacing2"),
        "tab_style": (str, "tabstyle"),
        "track_history": (bool, "undo"),
        "width": ScreenDistance,
        "wrap": Wrap,
    }

    def __init__(
        self,
        parent: TkWidget,
        *,
        bg_color: Color | None = None,
        caret_color: Color | None = None,
        caret_offtime: int | None = None,
        caret_ontime: int | None = None,
        caret_style: str = CaretStyle.Beam,
        caret_width: int | ScreenDistance | None = None,
        fg_color: Color | None = None,
        focusable: bool | None = None,
        font: Font | tuple[str | int | bool] | None = None,
        height: int | ScreenDistance | None = None,
        inactive_caret_style: str | None = None,
        inactive_selection_bg: Color | None = None,
        overflow: tuple[bool | str, bool | str] = ("auto", "auto"),
        padding: int | tuple[int] | tuple[int, int] | None = None,
        resize_along_chars: bool | None = None,
        selection_bg: Color | None = None,
        selection_fg: Color | None = None,
        space_after_paragraph: int | ScreenDistance | None = None,
        space_before_paragraph: int | ScreenDistance | None = None,
        space_before_wrapped_line: int | ScreenDistance | None = None,
        tab_stops: TabStop | list[TabStop] | None = None,
        tab_style: str | None = None,
        track_history: bool | None = None,
        width: int | ScreenDistance | None = None,
        wrap: Wrap | None = None,
        _peer_of: TextBox | None = None,
    ) -> None:

        if not font:
            font = Font("TkFixedFont")

        if caret_offtime is not None:
            caret_offtime = int(caret_offtime * 1000)

        if caret_ontime is not None:
            caret_ontime = int(caret_ontime * 1000)

        self.peer_of = _peer_of

        to_call = {
            "autoseparators": True,
            "highlightthickness": 0,
            "relief": "flat",
            "background": bg_color,
            "blockcursor": caret_style,
            "font": font,
            "foreground": fg_color,
            "height": height,
            "inactiveselectbackground": inactive_selection_bg,
            "insertbackground": caret_color,
            "insertofftime": caret_offtime,
            "insertontime": caret_ontime,
            "insertunfocussed": inactive_caret_style,
            "insertwidth": caret_width,
            "selectbackground": selection_bg,
            "selectforeground": selection_fg,
            "setgrid": resize_along_chars,
            "spacing1": space_before_paragraph,
            "spacing2": space_before_wrapped_line,
            "spacing3": space_after_paragraph,
            "tabstyle": tab_style,
            "takefocus": focusable,
            "undo": track_history,
            "width": width,
            "wrap": wrap,
        }

        if _peer_of is None:
            self._frame = Frame(parent)
            BaseWidget.__init__(self, self._frame, None, **to_call)
        else:
            self._frame = Frame(_peer_of._frame.parent)
            _name = f"{self._frame._name}.textbox_peer_{_peer_of.peer_count}_of_{_peer_of._name.split('.')[-1]}"
            BaseWidget.__init__(self, self._frame, (_peer_of, "peer", "create", _name), **to_call)
            self._name = _name

        self.padding = padding
        self.tab_stops = tab_stops

        self.peer_count: int = 0

        Tcl.eval(
            None,
            f"grid rowconfigure {self._frame._name} 0 -weight 1 \n"
            + f"grid columnconfigure {self._frame._name} 0 -weight 1 \n"
            + f"grid {self._name} -row 0 -column 0 -sticky nsew",
        )
        if overflow is not None:
            self.overflow = overflow

        self.index = TextIndex
        self.range = TextRange
        self.Tag = Tag
        self.marks = TextMarks()
        self.history = TextHistory()
        for attr in (self.index, self.range, self.Tag, self.marks, self.history):
            setattr(attr, "_widget", self)

        self.layout = self._frame.layout

    def _make_hor_scroll(self, hide: bool = True) -> None:
        self._h_scroll = ScrollBar(self._frame, orientation="horizontal", auto_hide=hide)
        self._h_scroll.attach(self)
        self._h_scroll.layout.grid(row=1, hor_align="stretch")

    def _make_vert_scroll(self, hide: bool = True) -> None:
        self._v_scroll = ScrollBar(self._frame, orientation="vertical", auto_hide=hide)
        self._v_scroll.attach(self)
        self._v_scroll.layout.grid(col=1, vert_align="stretch")

    def _convert_indices_or_range_to_tcl(self, indices) -> tuple[str, str]:
        if len(indices) == 1:
            index_or_range = indices[0]

            if isinstance(index_or_range, self.range):
                return tuple(index.__to_tcl__() for index in index_or_range)
            elif isinstance(index_or_range, self.index):
                return index_or_range.__to_tcl__(), index_or_range.forward(chars=1).__to_tcl__()
            elif isinstance(index_or_range, tuple):
                return (
                    self.index(*index_or_range).__to_tcl__(),
                    self.index(*index_or_range).forward(chars=1).__to_tcl__(),
                )
        elif len(indices) == 2:
            return tuple(index.__to_tcl__() for index in self.range(*indices))
        else:
            return "1.0", "end - 1 chars"

    def __len__(self) -> int:
        return self.end.line

    def __matmul__(
        self, index: tuple[int, int] | int | Icon | Image.Image | TkWidget
    ) -> TextBox.index:
        return self.index(index)

    def __contains__(self, text: str) -> bool:
        return text in self.get()

    def __getitem__(self, index: slice | tuple | TextBox.index) -> str:
        if isinstance(index, slice):
            return self.get(self.range(index))
        elif isinstance(index, (tuple, self.index)):
            return self.get(index)
        raise TypeError("expected a tuple, a slice or a TextBox.index object")

    @property
    def padding(self):
        return self._get(int, "padx"), self._get(int, "pady")

    @padding.setter
    def padding(self, new_padding: int | tuple[int, int] | list[int]) -> None:
        if new_padding is None:
            return

        padx = pady = None

        if isinstance(new_padding, int):
            padx = pady = new_padding
        elif len(new_padding) == 1:
            padx = pady = new_padding[0]
        elif len(new_padding) == 2:
            padx, pady = new_padding
        else:
            raise ValueError("4 side padding isn't supported for TextBox")

        self._set(padx=padx, pady=pady)

    def Peer(self, **kwargs):
        if self.peer_of is None:
            self.peer_count += 1
            return TextBox(_peer_of=self, **kwargs)
        else:
            raise RuntimeError("can't create a peer of a peer")

    @property
    def start(self) -> TextIndex:
        return self.index(0, no_check=True)

    @property
    def end(self) -> TextIndex:
        return self.index("end - 1 chars", no_check=True)

    @property
    def caret_pos(self) -> TextIndex:
        return self.marks["insert"]

    @caret_pos.setter
    def caret_pos(self, new_pos: TextIndex) -> None:
        self.marks["insert"] = new_pos

    @property
    def mouse_pos(self) -> TextIndex:
        return self.index("current")

    def coord_to_index(self, x, y) -> TextIndex:
        return self.index(f"@{int(x)},{int(y)}")

    @property
    def is_empty(self):
        return self.end == (1, 0)

    def insert(self, index: TextIndex | str = "insert", content: str = "", **kwargs) -> None:
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
            to_call = ("image", "create", index, *Tcl.to_tcl_args(image=content, padx=padx, pady=pady, align=align))
            # fmt: on
        elif isinstance(content, TkWidget):
            if content is self._frame.parent:
                # don't insert the textbox's parent in itself
                return

            margin = kwargs.pop("margin", None)
            padx = pady = None
            if margin is not None:
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
            to_call = ("window", "create", index, *Tcl.to_tcl_args(window=content, padx=padx, pady=pady, align=align, stretch=stretch))
            # fmt: on
        elif isinstance(content, Path):
            with content.resolve().open() as file:
                to_call = ("insert", index, file.read())
        else:
            to_call = ("insert", index, content)

        if kwargs:
            raise TypeError(f"insert() got unexpected keyword argument(s): {tuple(kwargs.keys())}")
        Tcl.call(None, self, *to_call)

    def delete(self, *indexes) -> None:
        Tcl.call(None, self, "delete", *self._convert_indices_or_range_to_tcl(indexes))

    def get(self, *indexes) -> str:
        return Tcl.call(str, self, "get", *self._convert_indices_or_range_to_tcl(indexes))

    def replace(self, *args, tag: Tag | None = None) -> None:
        if isinstance(args[0], TextRange) and isinstance(args[1], str):
            start, end = args[0]
            text = args[1]
        elif (
            len(args) == 3
            and isinstance(args[0], self.index)
            and isinstance(args[1], self.index)
            and isinstance(args[2], str)
        ):
            start = self.start if args[0] is None else args[0]
            end = self.end if args[1] is None else args[1]
            text = args[2]
        else:
            raise ValueError("invalid arguments. See help(TextBox.replace).")

        Tcl.call(None, self, "replace", start, end, text, tag)

    def search(
        self,
        pattern: str,
        start: TextIndex,
        stop: TextIndex | str = "end",
        *,
        backwards: bool = False,
        case_sensitive: bool = True,
        count_hidden: bool = False,
        exact: bool = False,
        forwards: bool = False,
        match_newline: bool = False,
        regex: bool = False,
        strict_limits: bool = False,
        variable: Integer = None,
    ):

        if stop == self.end:
            stop = "end - 1 chars"

        if variable is None:
            variable = Integer()

        to_call: list[str] = []

        if backwards:
            to_call += "-backwards"
        if not case_sensitive:
            to_call += "-nocase"
        if count_hidden:
            to_call += "-elide"
        if exact:
            to_call += "-exact"
        if forwards:
            to_call += "-forwards"
        if match_newline:
            to_call += "-nolinestop"
        if regex:
            to_call += "-regexp"
        if strict_limits:
            to_call += "-strictlimits"

        if pattern and pattern[0] == "-":
            to_call += "--"

        while True:
            result = Tcl.call(
                str, self._name, "search", "-count", variable, *to_call, pattern, start, stop
            )
            if not result:
                break
            yield self.range(self.index(result), self.index(result).forward(chars=variable.get()))  # type: ignore
            start = result + "+ 1 chars"

    def scroll_to(self, index: TextIndex) -> None:
        Tcl.call(None, self, "see", index)

    @property
    def overflow(self) -> tuple[bool | str, bool | str]:
        return self._overflow

    @overflow.setter
    def overflow(self, new_overflow: tuple[bool | str, bool | str]) -> None:
        if hasattr(self, "_h_scroll"):
            self._h_scroll.destroy()
        if hasattr(self, "_v_scroll"):
            self._v_scroll.destroy()

        if len(new_overflow) == 1:
            new_overflow = (new_overflow[0], new_overflow[0])

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
    def text(self) -> str:
        return self.get()

    @text.setter
    def text(self, new_text: str) -> None:
        self.delete()
        self.insert(self.end, new_text)

    @property
    def content(self) -> list[tuple[TextIndex, str | Tag | Icon | Image.Image | TkWidget]]:
        result = []  # type: ignore
        unclosed_tags = {}

        def add_item(type: str, value: str, index: str) -> None:
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
                            Tag.__from_tcl__(value),
                        ),
                    )
                    return

            convert = {
                "image": lambda x: _images[x],
                "mark": lambda x: f"TextBox.marks[{x!r}]",
                "text": str,
                "window": TkWidget.__from_tcl__,
            }[type]

            result.append((self.index(index), convert(value)))  # type: ignore  # "object" not callable

        Tcl.call(str, self, "dump", "-all", "-command", add_item, "1.0", "end - 1 chars")
        return result

    @Tcl.update_before
    def line_info(self, index: TextIndex) -> LineInfo:
        """Returns the accurate height only if the TextBox widget has already laid out"""
        result = Tcl.call(
            (ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance),
            self,
            "dlineinfo",
            index,
        )

        return LineInfo(*result)

    def range_info(self, *indexes) -> RangeInfo:
        result = Tcl.call(
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
            *self._convert_indices_or_range_to_tcl(indexes),
        )

        return RangeInfo(*result)
