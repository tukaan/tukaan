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
        value: bool = False,
        width: Optional[int] = None,
    ) -> None:
        self._variable = Boolean(value)
        
        BaseWidget.__init__(
            self,
            parent,
            command=on_click,
            offvalue=False,
            onvalue=True,
            style=style,
            takefocus=focusable,
            underline=underline,
            variable=self._variable,
            width=width,
        )
        self.config(text=text)

    def invoke(self):
        self._tcl_call(None, self, "invoke")

    def select(self):
        self._variable.set(True)

    def deselect(self):
        self._variable.set(False)

    def toggle(self):
        self._variable.set(not self._variable.get())

    @property
    def is_selected(self) -> bool:
        return self._variable.get()

    @is_selected.setter
    def is_selected(self, is_selected: bool) -> None:
        self._variable.set(is_selected)

    value = is_selected  # for consistency with RadioButton
