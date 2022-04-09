from typing import Literal, Optional

from ._base import BaseWidget, OutputDisplayWidget, TkWidget


class Separator(BaseWidget, OutputDisplayWidget):
    _tcl_class = "ttk::separator"
    _keys = {"orientation": (str, "orient")}

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
    ) -> None:
        BaseWidget.__init__(self, parent, orient=orientation)

    def _repr_details(self):
        return f"orientation={self.orientation!r}"
