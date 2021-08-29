from typing import Any, Callable, Dict, Tuple, Union

from ._base import BaseWidget, TukaanWidget
from ._returntype import Callback


class Button(BaseWidget):
    _keys = {
        "callback": (Callable, "command"),
        "default": str,
        "focusable": (bool, "takefocus"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        parent: Union[TukaanWidget, None] = None,
        callback: Union[Callable, None] = None,
        default: Union[str, None] = None,
        focusable: Union[bool, None] = None,
        style: Union[str, None] = None,
        text: Union[str, None] = None,
        underline: Union[int, None] = None,
        width: Union[int, None] = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            "ttk::button",
            command=callback,
            default=default,
            style=style,
            takefocus=focusable,
            text=text,
            width=width,
            underline=underline,
        )

    def invoke(self):
        return self._tcl_call(None, self, "invoke")
