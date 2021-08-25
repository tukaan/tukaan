from typing import Any, Callable, Dict, Tuple, Union

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    _keys: Dict[str, Union[Any, Tuple[Any, str]]] = {
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
        parent: Union[TkWidget, None] = None,
        callback: Union[Callable, None] = None,
        default: str = None,
        focusable: bool = None,
        style: str = None,
        text: str = None,
        underline: int = None,
        width: int = None,
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
