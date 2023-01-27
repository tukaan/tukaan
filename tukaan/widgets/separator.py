from __future__ import annotations

from tukaan._base import OutputDisplay, TkWidget, WidgetBase
from tukaan._cursors import Cursor_T, Cursors
from tukaan._props import CursorProp, OrientProp
from tukaan.enums import Orientation


class Separator(WidgetBase, OutputDisplay):
    _tcl_class = "ttk::separator"

    cursor = CursorProp()
    orientation = OrientProp()

    def __init__(
        self,
        parent: TkWidget,
        cursor: Cursor_T = Cursors.DEFAULT,
        orientation: Orientation | None = None,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, cursor=cursor, orient=orientation, tooltip=tooltip)

    def _repr_details(self):
        return f"orientation={self.orientation!r}"
