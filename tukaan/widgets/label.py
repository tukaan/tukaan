from __future__ import annotations

from PIL import Image  # type: ignore

from tukaan._base import OutputDisplay, TkWidget, WidgetBase
from tukaan._images import Icon, image
from tukaan._props import bg_color, cget, config, focusable, image_pos, text, text_align
from tukaan.colors import Color
from tukaan.enums import Anchor, ImagePosition, Justify


class Label(WidgetBase, OutputDisplay):
    _tcl_class = "ttk::label"

    bg_color = bg_color
    focusable = focusable
    image = image
    image_pos = image_pos
    text = text
    text_align = text_align

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        *,
        bg_color: Color | str | None = None,
        content_align: Anchor = Anchor.Center,
        fg_color: Color | str | None = None,
        focusable: bool | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition | None = None,
        max_line_length: int | None = None,
        text_align: Justify = Justify.Left,
    ) -> None:

        WidgetBase.__init__(
            self,
            parent,
            anchor=content_align,
            background=bg_color,
            compound=image_pos,
            foreground=fg_color,
            image=image,
            justify=text_align,
            takefocus=focusable,
            text=text,
            wraplength=max_line_length,
        )

    @property
    def content_align(self) -> Anchor:
        return cget(self, Anchor, "-anchor")

    @content_align.setter
    def content_align(self, value: Anchor) -> None:
        config(self, anchor=value)

    @property
    def max_line_length(self) -> int:
        return cget(self, int, "-wraplength")

    @max_line_length.setter
    def max_line_length(self, value: int) -> None:
        config(self, wraplength=value)
