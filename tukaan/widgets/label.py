from __future__ import annotations

from typing import Literal, Optional

from PIL import Image  # type: ignore

from ._base import BaseWidget, TkWidget
from tukaan._constants import _anchors, _image_positions
from tukaan._images import Icon, _image_converter_class
from tukaan._structures import Color


class Label(BaseWidget):
    _tcl_class = "ttk::label"
    _keys = {
        "align_content": _anchors,
        "align_text": str,
        "focusable": (bool, "takefocus"),
        "image": _image_converter_class,
        "image_pos": (_image_positions, "compound"),
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
        "bg_color": (Color, "background"),
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        text: Optional[str] = None,
        *,
        align_content: Optional[str] = None,
        align_text: Optional[Literal["left", "center", "right"]] = None,
        bg_color: Optional[str] = None,
        fg_color: Optional[str] = None,
        focusable: Optional[bool] = None,
        image: Optional[Image.Image | Icon] = None,
        image_pos: Optional[str] = None,
        max_line_length: Optional[int] = None,
        style: Optional[str] = None,
    ) -> None:

        if align_content is not None:
            # can't use "" as anchor, so have to check if it's None
            # error: ambiguous anchor "": must be ...
            align_content = _anchors[align_content]

        BaseWidget.__init__(
            self,
            parent,
            anchor=align_content,
            compound=_image_positions[image_pos],
            image=image,
            justify=align_text,
            style=style,
            takefocus=focusable,
            wraplength=max_line_length,
            background=bg_color,
            foreground=fg_color,
        )
        self.config(text=text)
