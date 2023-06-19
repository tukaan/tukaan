from __future__ import annotations

from tukaan._base import TkWidget, Widget
from tukaan._properties import EnumDesc
from tukaan.enums import Orientation


class Divider(Widget, widget_cmd="ttk::separator", tk_class="TSeparator"):
    orientation = EnumDesc("orient", Orientation, False)

    def __init__(self, parent: TkWidget, orientation: Orientation | None = None) -> None:
        super().__init__(parent, orient=orientation)


class Label:
    ...
