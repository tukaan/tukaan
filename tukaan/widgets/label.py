from __future__ import annotations

from PIL import Image  # type: ignore

from tukaan._base import OutputDisplay, TkWidget, WidgetBase
from tukaan._images import Icon, ImageProp
from tukaan._props import (
    BackgroundProp,
    FocusableProp,
    ImagePositionProp,
    TextAlignProp,
    TextProp,
    cget,
    config,
)
from tukaan.colors import Color
from tukaan.enums import Anchor, ImagePosition, Justify
from tukaan.fonts.font import Font, FontProp


class Label(WidgetBase, OutputDisplay):
    _tcl_class = "ttk::label"

    bg_color = BackgroundProp()
    focusable = FocusableProp()
    font = FontProp()
    image = ImageProp()
    image_pos = ImagePositionProp()
    text = TextProp()
    text_align = TextAlignProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        *,
        bg_color: Color | str | None = None,
        content_align: Anchor = Anchor.Center,
        fg_color: Color | str | None = None,
        focusable: bool | None = None,
        font: Font | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition | None = None,
        max_line_length: int | None = None,
        text_align: Justify = Justify.Left,
        tooltip: str | None = None,
    ) -> None:

        WidgetBase.__init__(
            self,
            parent,
            anchor=content_align,
            background=bg_color,
            compound=image_pos,
            font=font,
            foreground=fg_color,
            image=image,
            justify=text_align,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
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
