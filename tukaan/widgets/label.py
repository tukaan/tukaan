from __future__ import annotations

from PIL import Image  # type: ignore

from tukaan._enums import Alignment, ImagePosition, Justify
from tukaan._images import Icon, PIL_TclConverter
from tukaan.colors import Color

from ._base import BaseWidget, OutputDisplayWidget, TkWidget


class Label(BaseWidget, OutputDisplayWidget):
    _tcl_class = "ttk::label"
    _keys = {
        "align_content": Alignment,
        "align_text": Justify,
        "focusable": (bool, "takefocus"),
        "image": PIL_TclConverter,
        "image_pos": (ImagePosition, "compound"),
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
        "bg_color": (Color, "background"),
    }

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        *,
        align_content: Alignment = Alignment.Center,
        bg_color: str | None = None,
        fg_color: str | None = None,
        focusable: bool | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition | None = None,
        justify: Justify | None = None,
        max_line_length: int | None = None,
        style: str | None = None,
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
