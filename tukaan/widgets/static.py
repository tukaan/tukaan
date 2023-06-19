from __future__ import annotations

from PIL import Image  # type: ignore

from tukaan._base import TkWidget, Widget
from tukaan._images import ImageProp
from tukaan._properties import EnumDesc, FocusableProp, IntDesc, StrDesc, cget, config
from tukaan.enums import Anchor, ImagePosition, Justify, Orientation


class Divider(Widget, widget_cmd="ttk::separator", tk_class="TSeparator"):
    orientation = EnumDesc("orient", Orientation, False)

    def __init__(self, parent: TkWidget, orientation: Orientation | None = None) -> None:
        super().__init__(parent, orient=orientation)


class Label(Widget, widget_cmd="ttk::label", tk_class="TLabel"):
    align = EnumDesc("anchor", Anchor, False)
    focusable = FocusableProp()
    image = ImageProp()
    image_pos = EnumDesc("compound", ImagePosition)
    justify = EnumDesc(enum=Justify, allow_None=False)
    max_line_length = IntDesc("wraplength")
    text = StrDesc()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        *,
        align: Anchor = Anchor.Center,
        focusable: bool | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition = ImagePosition.Above,
        justify: Justify = Justify.Left,
        max_line_length: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            anchor=align,
            compound=image_pos,
            image=image,
            justify=justify,
            takefocus=focusable,
            text=text,
            wraplength=max_line_length,
        )
