from typing import Literal, Union

from ._base import BaseWidget, TukaanWidget
from ._constants import _anchors
from ._returntype import DictKey


class Label(BaseWidget):
    _keys = {
        "anchor": DictKey(_anchors),
        "focusable": (bool, "takefocus"),
        "justify": str,
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
    }

    def __init__(
        self,
        parent: Union[TukaanWidget, None] = None,
        anchor: Union[
            Literal["none"],
            None,
        ] = None,
        focusable: Union[bool, None] = None,
        justify: Union[Literal["left", "center", "right"], None] = None,
        max_line_length: Union[int, None] = None,
        style: Union[str, None] = None,
        text: Union[str, None] = None,
    ) -> None:

        if anchor is not None:
            anchor = _anchors[anchor]

        BaseWidget.__init__(
            self,
            parent,
            "ttk::label",
            anchor=anchor,
            takefocus=focusable,
            justify=justify,
            wraplength=max_line_length,
            style=style,
            text=text,
        )
