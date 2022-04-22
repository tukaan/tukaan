from __future__ import annotations

from typing import Callable

from PIL import Image  # type: ignore

from tukaan._enums import ImagePosition
from tukaan._images import Icon, PIL_TclConverter
from tukaan._tcl import Tcl

from ._base import BaseWidget, InputControlWidget, TkWidget


class Button(BaseWidget, InputControlWidget):
    _tcl_class = "ttk::button"
    _keys = {
        "default": str,
        "focusable": (bool, "takefocus"),
        "image": PIL_TclConverter,
        "image_pos": (ImagePosition, "compound"),
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        on_click: Callable | None = None,
        *,
        default: str | None = None,
        focusable: bool | None = None,
        image: Image.Image | Icon | None = None,
        image_pos: ImagePosition | None = None,
        style: str | None = None,
        underline: int | None = None,
        width: int | None = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            compound=image_pos,
            default=default,
            image=image,
            style=style,
            takefocus=focusable,
            underline=underline,
            width=width,
        )
        self.config(text=text)

    def invoke(self):
        Tcl.call(None, self, "invoke")
