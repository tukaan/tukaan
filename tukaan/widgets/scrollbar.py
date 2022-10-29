from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import FocusableProp, OrientProp, config
from tukaan._tcl import Tcl
from tukaan.enums import Orientation
from tukaan.exceptions import WidgetError


class ScrollBar(WidgetBase, InputControl):
    _tcl_class = "ttk::scrollbar"

    focusable = FocusableProp()
    orientation = OrientProp()

    _hidden = False

    def __init__(
        self,
        parent: TkWidget,
        orientation: Orientation | None = None,
        *,
        auto_hide: bool = True,
        focusable: bool | None = None,
        tooltip: str | None = None,
    ) -> None:
        self._auto_hide = auto_hide

        WidgetBase.__init__(self, parent, orient=orientation, takefocus=focusable, tooltip=tooltip)

    def _set_command(self, value: Callable) -> None:
        config(self, command=value)

    def _set_range(self, start: str, end: str) -> None:
        if self._auto_hide:
            should_be_hidden = float(start) <= 0.0 and float(end) >= 1.0

            if should_be_hidden and not self._hidden:
                self.hide()
                self._hidden = True
            elif not should_be_hidden and self._hidden:
                self.unhide()
                self._hidden = False

        Tcl.call(None, self, "set", start, end)

    def attach(self, widget: WidgetBase) -> None:
        if self.orientation is Orientation.Horizontal:
            try:
                widget.on_xscroll = self._set_range
                self._set_command(widget.x_scroll)
            except AttributeError as e:
                raise WidgetError("this widget isn't scrollable horizontally") from e

        elif self.orientation is Orientation.Vertical:
            try:
                widget.on_yscroll = self._set_range
                self._set_command(widget.y_scroll)
            except AttributeError as e:
                raise WidgetError("this widget isn't scrollable vertically") from e

    @property
    def auto_hide(self) -> bool:
        return self._auto_hide

    @auto_hide.setter
    def auto_hide(self, value: bool) -> None:
        self._auto_hide = value
