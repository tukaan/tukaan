from __future__ import annotations

from ._base import BaseWidget, OutputDisplayWidget, TkWidget


class Separator(BaseWidget, OutputDisplayWidget):
    _tcl_class = "ttk::separator"
    _keys = {"orientation": (str, "orient")}

    def __init__(
        self,
        parent: TkWidget,
        orientation: str | None = None,
    ) -> None:
        BaseWidget.__init__(self, parent, orient=orientation)

    def _repr_details(self):
        return f"orientation={self.orientation!r}"
