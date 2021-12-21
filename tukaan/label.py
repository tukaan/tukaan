from typing import Literal, Optional

from ._base import BaseWidget, TkWidget
from ._constants import _anchors


class Label(BaseWidget):
    _tcl_class = "ttk::label"
    _keys = {
        "align_content": _anchors,
        "focusable": (bool, "takefocus"),
        "align_text": str,
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        align_content: Optional[str] = None,
        focusable: Optional[bool] = None,
        align_text: Optional[Literal["left", "center", "right"]] = None,
        max_line_length: Optional[int] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
    ) -> None:

        if align_content is not None:
            # can't use "" as anchor, so have to check if it's None
            # error: ambiguous anchor "": must be ...
            align_content = _anchors[align_content]

        BaseWidget.__init__(
            self,
            parent,
            anchor=align_content,
            takefocus=focusable,
            justify=align_text,
            wraplength=max_line_length,
            style=style,
            text=text,
        )
