from __future__ import annotations

from typing import Literal, Optional

from PIL import Image

from ._base import BaseWidget, TkWidget
from ._constants import _anchors
from ._images import _image_converter_class, Icon


class Label(BaseWidget):
    _tcl_class = "ttk::label"
    _keys = {
        "align_content": _anchors,
        "align_text": str,
        "focusable": (bool, "takefocus"),
        "image": _image_converter_class,
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        align_content: Optional[str] = None,
        align_text: Optional[Literal["left", "center", "right"]] = None,
        focusable: Optional[bool] = None,
        image: Optional[Image.Image | Icon] = None,
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
            image=image,
            justify=align_text,
            style=style,
            takefocus=focusable,
            wraplength=max_line_length,
        )
        self.config(text=text)
