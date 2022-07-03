from __future__ import annotations

from typing import Callable

from PIL import Image  # type: ignore

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._images import Icon
from tukaan._props import command, focusable, image_pos, text, width
from tukaan._tcl import Tcl
from tukaan.enums import ImagePosition


class Button(WidgetBase, InputControl):
    _tcl_class = "ttk::button"

    focusable = focusable
    image_pos = image_pos
    on_click = command
    text = text
    width = width

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        on_click: Callable | None = None,
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
            command=on_click,
            compound=image_pos,
            image=image,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            width=width,
        )

    def invoke(self) -> None:
        """Invokes the button, as if it were clicked"""

        Tcl.call(None, self, "invoke")
