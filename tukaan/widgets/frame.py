from __future__ import annotations

from tukaan._base import Container, TkWidget, WidgetBase
from tukaan._props import PaddingProp


class Frame(WidgetBase, Container):
    _tcl_class = "ttk::frame"

    padding = PaddingProp()

    def __init__(
        self,
        parent: TkWidget,
        padding: int | tuple[int, ...] | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, tooltip=tooltip)

        self.padding = padding
