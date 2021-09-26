from typing import Literal, Optional

from ._base import BaseWidget, TkWidget


class Scrollbar(BaseWidget):
    _keys = {
        "focusable": (bool, "takefocus"),
        "orientation": (str, "orient"),
        "scrollcommand": ("func", "command"),
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        focusable: Optional[bool] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
    ) -> None:
        BaseWidget.__init__(
            self, parent, "ttk::scrollbar", orient=orientation, takefocus=focusable
        )

    def attach(self, widget: BaseWidget):
        if self.orientation == "vertical":
            try:
                widget.config(on_yscroll=self.set)
            except KeyError:
                raise RuntimeError(
                    f"can't attach scrollbar, {widget} is not scrollable in y direction"
                )
            self.config(scrollcommand=widget.y_scroll)
        elif self.orientation == "horizontal":
            try:
                widget.config(on_xscroll=self.set)
            except KeyError:
                raise RuntimeError(
                    f"can't attach scrollbar, {widget} is not scrollable in x direction"
                )
            self.config(scrollcommand=widget.x_scroll)

    def set(self, first, last) -> None:
        self._tcl_call(None, self, "set", first, last)

    def get(self) -> None:
        return self._tcl_call((float,), self, "get")
