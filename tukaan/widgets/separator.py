from __future__ import annotations

from tukaan._base import OutputDisplay, TkWidget, WidgetBase
from tukaan._props import OrientProp
from tukaan.enums import Orientation


class Separator(WidgetBase, OutputDisplay):
    _tcl_class = "ttk::separator"

    orientation = OrientProp()

    def __init__(self, parent: TkWidget, orientation: Orientation | None = None, **kwargs) -> None:
        WidgetBase.__init__(self, parent, orient=orientation, **kwargs)

    def _repr_details(self):
        return f"orientation={self.orientation!r}"
