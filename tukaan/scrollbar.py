from typing import Literal, Optional

from ._base import BaseWidget, TkWidget


class Scrollbar(BaseWidget):
    _tcl_class = "ttk::scrollbar"
    _keys = {
        "focusable": (bool, "takefocus"),
        "orientation": (str, "orient"),
        "scrollcommand": ("func", "command"),
    }

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        auto_hide: bool = True,
        focusable: Optional[bool] = None,
        orientation: Optional[Literal["horizontal", "vertical"]] = None,
    ) -> None:
        self._auto_hide = auto_hide

        BaseWidget.__init__(self, parent, orient=orientation, takefocus=focusable)

    @property
    def auto_hide(self):
        return self._auto_hide

    @auto_hide.setter
    def auto_hide(self, should_auto_hide: bool) -> None:
        self._auto_hide = should_auto_hide

    def attach(self, widget: BaseWidget):
        if self.orientation == "vertical":
            try:
                widget.config(on_yscroll=self.set)
            except KeyError:
                raise RuntimeError(f"can't attach scrollbar, {widget} is not scrollable vertically")
            self.config(scrollcommand=widget.y_scroll)
        elif self.orientation == "horizontal":
            try:
                widget.config(on_xscroll=self.set)
            except KeyError:
                raise RuntimeError(
                    f"can't attach scrollbar, {widget} is not scrollable horizontally"
                )
            self.config(scrollcommand=widget.x_scroll)

    def set(self, start: float, end: float) -> None:
        if self._auto_hide:
            if float(start) <= 0.0 and float(end) >= 1.0:
                self.hide()
            else:
                self.unhide()
        self._tcl_call(None, self, "set", start, end)

    def get(self) -> None:
        return self._tcl_call((float,), self, "get")
