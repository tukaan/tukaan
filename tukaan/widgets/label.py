from __future__ import annotations

from typing import Optional

from PIL import Image  # type: ignore

from tukaan._enums import Alignment, ImagePosition, Justify
from tukaan._images import Icon, _image_converter_class
from tukaan._structures import Color

from ._base import BaseWidget, OutputDisplayWidget, TkWidget


class Label(BaseWidget, OutputDisplayWidget):
    _tcl_class = "ttk::label"
    _keys = {
        "align_content": Alignment,
        "align_text": Justify,
        "focusable": (bool, "takefocus"),
        "image": _image_converter_class,
        "image_pos": (ImagePosition, "compound"),
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
        align_content: Alignment = Alignment.Center,
        bg_color: Optional[str] = None,
        fg_color: Optional[str] = None,
        focusable: Optional[bool] = None,
        image: Optional[Image.Image | Icon] = None,
        image_pos: Optional[ImagePosition] = None,
        justify: Optional[Justify] = None,
        max_line_length: Optional[int] = None,
        style: Optional[str] = None,
    ) -> None:

        BaseWidget.__init__(
            self,
            parent,
            anchor=align_content,
            compound=image_pos,
            image=image,
            justify=justify,
            style=style,
            takefocus=focusable,
            wraplength=max_line_length,
            background=bg_color,
            foreground=fg_color,
        )
        self.config(text=text)
