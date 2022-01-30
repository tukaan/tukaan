from __future__ import annotations

from typing import Callable, Optional

from PIL import Image  # type: ignore

from ._base import BaseWidget, TkWidget
from ._images import Icon, _image_converter_class


class Button(BaseWidget):
    _tcl_class = "ttk::button"
    _keys = {
        "default": str,
        "focusable": (bool, "takefocus"),
        "image": _image_converter_class,
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        default: Optional[str] = None,
        focusable: Optional[bool] = None,
        image: Optional[Image.Image | Icon] = None,
        on_click: Optional[Callable] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
        underline: Optional[int] = None,
        width: Optional[int] = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            default=default,
            image=image,
            style=style,
            takefocus=focusable,
            underline=underline,
            width=width,
        )
        self.config(text=text)

    def invoke(self):
        self._tcl_call(None, self, "invoke")
