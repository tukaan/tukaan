from typing import Callable, Optional

from ._base import BaseWidget, TkWidget
from ._variables import Boolean


class CheckBox(BaseWidget):
    """To turn it on or off you have to use a control variable"""

    _tcl_class = "ttk::checkbutton"
    _keys = {
        "focusable": (bool, "takefocus"),
        "on_click": ("func", "command"),
        "style": str,
        "text": str,
        "underline": int,
        "variable": Boolean,
        "width": int,
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        focusable: Optional[bool] = None,
        on_click: Optional[Callable] = None,
        style: Optional[str] = None,
        text: Optional[str] = None,
        underline: Optional[int] = None,
        variable: Optional[Boolean] = None,
        width: Optional[int] = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            offvalue=False,
            onvalue=True,
            style=style,
            takefocus=focusable,
            underline=underline,
            variable=variable,
            width=width,
        )
        self.config(text=text)

    def toggle(self):
        """Also invokes the on_click command"""
        self._tcl_call(None, self, "invoke")
