from __future__ import annotations

from typing import Callable, Optional

from PIL import Image  # type: ignore

from tukaan._enums import ImagePosition
from tukaan._images import Icon, _image_converter_class
from tukaan._tcl import Tcl

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    _tcl_class = "ttk::button"
    _keys = {
        "default": str,
        "focusable": (bool, "takefocus"),
        "image": _image_converter_class,
        "image_pos": (ImagePosition, "compound"),
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        text: Optional[str] = None,
        on_click: Optional[Callable] = None,
        *,
        default: Optional[str] = None,
        focusable: Optional[bool] = None,
        image: Optional[Image.Image | Icon] = None,
        image_pos: Optional[ImagePosition] = None,
        style: Optional[str] = None,
        underline: Optional[int] = None,
        width: Optional[int] = None,
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
