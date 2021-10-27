from __future__ import annotations

from collections import abc, namedtuple
from typing import Any, Iterator, Optional

from ._base import BaseWidget, TkWidget
from ._constants import _wraps
from ._misc import Color, Font, ScreenDistance
from ._utils import (
    ClassPropertyMetaClass,
    TukaanError,
    _callbacks,
    classproperty,
    counts,
    py_to_tcl_arguments,
    reversed_dict,
)


class Tag(metaclass=ClassPropertyMetaClass):
    _widget: TextBox
    _keys = {
        "background": Color,
        "first_line_margin": (ScreenDistance, "lmargin1"),
        "font": Font,
        "foreground": Color,
        "hanging_line_margin": (ScreenDistance, "lmargin2"),
        "hidden": (bool, "elide"),
        "justify": str,
        "offset": ScreenDistance,
        "right_side_margin": (ScreenDistance, "rmargin"),
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
        background=None,
        bold=False,
        first_line_margin=None,
        font=None,
        foreground=None,
        hanging_line_margin=None,
        hidden: Optional[bool] = None,
        italic=False,
        justify=None,
        offset=None,
        right_side_margin=None,
        space_after_paragraph=None,
        space_before_paragraph=None,
        space_before_wrapped_line=None,
        strikethrough: bool = False,
        tab_stops=None,
        underline: bool = False,
        wrap=None,
    ) -> None:
        self._name = (
            f"{self._widget.tcl_path}:tag_{next(counts['textbox_tag'])}" if _name is None else _name
        )

        self._call_tag_subcommand(
            None,
            "configure",
            background=background,
            elide=hidden,
            font=font,
            foreground=foreground,
            justify=justify,
            lmargin1=first_line_margin,
            lmargin2=hanging_line_margin,
            offset=offset,
            rmargin=right_side_margin,
            spacing1=space_before_paragraph,
            spacing2=space_before_wrapped_line,
            spacing3=space_after_paragraph,
            tabs=tab_stops,
            wrap=_wraps[wrap],
        )

    def __repr__(self) -> str:
        return f"<tukaan.TextBox tag named {self._name!r}>"

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

    def _cget(self, key: str) -> Any:
        if isinstance(self._keys[key], tuple):
            type_spec, key = self._keys[key]
        else:
            type_spec = self._keys[key]

        if type_spec == "func":
            # return a callable func, not tcl name
            result = self._call_tag_subcommand(str, "cget", f"-{key}")
            return _callbacks[result]

        if isinstance(type_spec, dict):
            result = self._call_tag_subcommand(str, "cget", f"-{key}")
            return reversed_dict(type_spec)[result]

        return self._call_tag_subcommand(type_spec, "cget", f"-{key}")

    def config(self, **kwargs) -> None:
        for key in tuple(kwargs.keys()):
            if isinstance(self._keys[key], tuple):
                # if key has a tukaan alias, use the tuple's 2-nd item as the tcl key
                kwargs[self._keys[key][1]] = kwargs.pop(key)

        self._call_tag_subcommand(None, "configure", *py_to_tcl_arguments(**kwargs))

    def _call_tag_subcommand(self, returntype: Any, subcommand: str, *args, **kwargs) -> Any:
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

        self._call_tag_subcommand(None, "add", start, end)

    def delete(self) -> None:
        self._call_tag_subcommand(None, "delete")

    def remove(self, start: TextIndex = None, end: TextIndex = None) -> None:
        start = self._widget.start if start is None else start
        end = self._widget.end if end is None else end

        self._call_tag_subcommand(None, "remove", start, end)

    @property
    def ranges(self):
        flat_pairs = map(self._widget.index.from_tcl, self._call_tag_subcommand((str,), "ranges"))
        return list(zip(flat_pairs, flat_pairs))

    @classproperty
    def hidden(cls) -> Tag:
        return cls(_name="hidden", hidden=True)


class TextIndex(namedtuple("TextIndex", "line column")):
    _widget: TextBox

    def __new__(cls, line: int = 1, column: int = 0) -> TextIndex:
        return super(TextIndex, cls).__new__(cls, line, column)  # type: ignore

    def to_tcl(self) -> str:
        return f"{self.line}.{self.column}"

    @classmethod
    def from_tcl(cls, string: str) -> TextIndex:
        result = cls._widget._tcl_call(str, cls._widget.tcl_path, "index", string)
        line, column = tuple(map(int, result.split(".")))
        return cls(line, column)

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

    def __contains__(self, mark: str) -> bool:
        return mark in self.__get_names()

    def __setitem__(self, name: str, index: TextIndex) -> None:
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "set", name, index)

    def __getitem__(self, name: str) -> TextIndex:
        if name not in self:
            raise KeyError(f"Mark {name!r} doesn't exists in {self._widget}")

        return self._widget.index.from_tcl(
            self._widget._tcl_call(str, self._widget.tcl_path, "index", name)
        )

    def __delitem__(self, name: str) -> None:
        if name == "insert":
            raise TukaanError("can't delete insertion cursor")
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "unset", name)


class TextBox(BaseWidget):
    _tcl_class = "text"
    _keys = {"font": Font, "wrap": _wraps}

    def __init__(
        self, parent: Optional[TkWidget] = None, wrap=None, font=("monospace", 10)
    ) -> None:
        assert wrap in _wraps, f"wrapping must be one of {tuple(_wraps.keys())}"
        wrap = _wraps[wrap]

        BaseWidget.__init__(self, parent, highlightthickness=0, relief="flat", font=font, wrap=wrap)

        self.index = TextIndex
        self.Tag = Tag
        self.marks = Marks()
        for attr in (self.index, self.marks, self.Tag):
            setattr(attr, "_widget", self)

    @property
    def start(self) -> TextIndex:
        return self.index()

    @property
    def end(self) -> TextIndex:
        return self._tcl_call(self.index, self, "index", "end - 1 char")

    def insert(self, index: TextIndex, content: str) -> None:
        self._tcl_call(None, self, "insert", index, content)

    def delete(self, start: TextIndex = None, end: TextIndex = None):
        start = self.start if start is None else start
        end = self.end if end is None else end

        return self._tcl_call(str, self, "delete", start, end)

    def get(self, start: TextIndex = None, end: TextIndex = None):
        start = self.start if start is None else start
        end = self.end if end is None else end

        return self._tcl_call(str, self, "get", start, end)

    def scroll_to(self, index: TextIndex) -> None:
        self._tcl_call(None, self, "see", index)

    @property
    def content(self):
        return self.get()

    @content.setter
    def content(self, new_content):
        self.delete()
        self.insert(self.end, new_content)
