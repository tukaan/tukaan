from __future__ import annotations

from typing import Callable

from tukaan._base import TkWidget, Widget
from tukaan._properties import IntDescriptor, StrDescriptor, FocusableProp, ActionProp
from tukaan._tcl import Tcl


class Button(Widget, widget_cmd="ttk::button", tk_class="TButton"):
    action = ActionProp()
    focusable = FocusableProp()
    text = StrDescriptor()
    width = IntDescriptor()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        action: Callable | None = None,
        *,
        focusable: bool | None = None,
        width: int | None = None,
    ) -> None:
        super().__init__(parent, command=action, takefocus=focusable, text=text, width=width)

    def invoke(self) -> None:
        """Invoke the button, as if it had been clicked."""
        Tcl.call(None, self, "invoke")
