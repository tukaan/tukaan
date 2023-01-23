from __future__ import annotations

from tukaan._base import Container, TkWidget, WidgetBase
from tukaan._cursors import Cursors
from tukaan._props import CursorProp, PaddingProp


class Frame(WidgetBase, Container):
    _tcl_class = "ttk::frame"

    cursor = CursorProp()
    padding = PaddingProp()

    def __init__(
        self,
        parent: TkWidget,
        cursor: Cursors = Cursors.DEFAULT,
        padding: int | tuple[int, ...] | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, cursor=cursor, tooltip=tooltip)

        self.padding = padding
