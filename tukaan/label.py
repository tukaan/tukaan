from typing import Literal, Optional

from ._base import BaseWidget, TkWidget
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
        parent: Optional[TkWidget] = None,
        anchor: Optional[str] = None,
        focusable: Optional[bool] = None,
        justify: Optional[Literal["left", "center", "right"]] = None,
        max_line_length: Optional[int] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
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
