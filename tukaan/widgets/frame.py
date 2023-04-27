from __future__ import annotations

from tukaan._base import Container, TkWidget, WidgetBase
from tukaan._props import PaddingProp


class Frame(WidgetBase, Container):
    _tcl_widget_name = "ttk::frame"
    _tk_class_name = "TFrame"

    padding = PaddingProp()

    def __init__(
        self,
        parent: TkWidget,
        padding: int | tuple[int, ...] | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, tooltip=tooltip)

        self.padding = padding
