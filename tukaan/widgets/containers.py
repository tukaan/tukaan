from __future__ import annotations

from tukaan._base import TkWidget, Widget
from tukaan._properties import PaddingProp


class Frame(Widget, widget_cmd="frame", tk_class="Frame"):
    def __init__(self, parent: TkWidget) -> None:
        Widget.__init__(self, parent)


class Panel(Widget, widget_cmd="ttk::frame", tk_class="TFrame"):
    padding = PaddingProp()

    def __init__(self, parent: TkWidget, padding: tuple[int, ...] | None = None) -> None:
        Widget.__init__(self, parent)

        self.padding = padding


class LabeledPanel:
    ...


class SplitView:
    ...


class TabView:
    ...
