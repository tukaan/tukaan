from typing import Callable, Optional

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    _keys = {
        "on_click": ("func", "command"),
        "default": str,
        "focusable": (bool, "takefocus"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        on_click: Optional[Callable] = None,
        default: Optional[str] = None,
        focusable: Optional[bool] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
        underline: Optional[int] = None,
        width: Optional[int] = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            "ttk::button",
            command=on_click,
            default=default,
            style=style,
            takefocus=focusable,
            text=text,
            width=width,
            underline=underline,
        )

    def invoke(self):
        self._tcl_call(None, self, "invoke")
