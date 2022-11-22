from __future__ import annotations

from typing import Callable

from PIL import Image  # type: ignore

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._images import Icon, ImageProp
from tukaan._props import CommandProp, FocusableProp, ImagePositionProp, TextProp, WidthProp
from tukaan._tcl import Tcl
from tukaan.enums import ImagePosition


class Button(WidgetBase, InputControl):
    _tcl_class = "ttk::button"

    action = CommandProp()
    focusable = FocusableProp()
    image = ImageProp()
    image_pos = ImagePositionProp()
    text = TextProp()
    width = WidthProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        action: Callable | None = None,
        *,
        focusable: bool | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition | None = None,
        tooltip: str | None = None,
        width: int | None = None,
    ) -> None:
        WidgetBase.__init__(
            self,
            parent,
            command=action,
            compound=image_pos,
            image=image,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            width=width,
        )

    def invoke(self) -> None:
        """Invoke the button, as if it were clicked."""
        Tcl.call(None, self, "invoke")
