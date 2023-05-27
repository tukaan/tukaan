from __future__ import annotations

from typing import Callable

from PIL.Image import Image

from tukaan._base import TkWidget, Widget
from tukaan._images import ImageProp
from tukaan._properties import ActionProp, FocusableProp, IntDesc, StrDesc
from tukaan._tcl import Tcl


class Button(Widget, widget_cmd="ttk::button", tk_class="TButton"):
    action = ActionProp()
    focusable = FocusableProp()
    text = StrDesc()
    width = IntDesc()
    image = ImageProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        action: Callable | None = None,
        *,
        focusable: bool | None = None,
        image: Image | None = None,
        width: int | None = None,
    ) -> None:
        super().__init__(
            parent, command=action, image=image, takefocus=focusable, text=text, width=width
        )

    def invoke(self) -> None:
        """Invoke the button, as if it had been clicked."""
        Tcl.call(None, self, "invoke")


class CheckBox:
    ...


class RadioButton:
    ...
