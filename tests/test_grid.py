import pytest

from tests.base import with_app_context
from tukaan._base import Widget
from tukaan.enums import Align
from tukaan.layouts.grid import convert_align_to_tk_sticky


def test_align_to_tk_sticky_converter():
    for align, sticky in [
        ((), ""),
        (Align.Center, ""),
        (None, ""),
        ((Align.Center, Align.Center), ""),
        ((Align.Center, Align.End), "s"),
        ((Align.Center, Align.Start), "n"),
        ((Align.Center, Align.Stretch), "ns"),
        ((Align.Center, None), ""),
        ((Align.End, Align.Center), "e"),
        ((Align.End, Align.End), "se"),
        ((Align.End, Align.Start), "ne"),
        ((Align.End, Align.Stretch), "nse"),
        ((Align.End, None), "e"),
        ((Align.Start, Align.Center), "w"),
        ((Align.Start, Align.End), "sw"),
        ((Align.Start, Align.Start), "nw"),
        ((Align.Start, Align.Stretch), "nsw"),
        ((Align.Start, None), "w"),
        ((Align.Stretch, Align.Center), "ew"),
        ((Align.Stretch, Align.End), "sew"),
        ((Align.Stretch, Align.Start), "new"),
        ((Align.Stretch, Align.Stretch), "nsew"),
        ((Align.Stretch, None), "ew"),
        ((None, Align.Center), ""),
        ((None, Align.End), "s"),
        ((None, Align.Start), "n"),
        ((None, Align.Stretch), "ns"),
        ((None, None), ""),
    ]:
        assert convert_align_to_tk_sticky(align) == sticky


class SimpleButton(Widget, widget_cmd="ttk::button", tk_class="TButton"):
    ...


class SimpleMegaWidget(Widget, widget_cmd="ttk::frame", tk_class="TFrame"):
    def __init__(self, parent: Widget) -> None:
        Widget.__init__(self, parent)
        self._button = SimpleButton(self)
        self._button.grid()
        self.finalize_megawidget(self._button._name)


@pytest.mark.xfail(reason="Need to figure out, how default row and col indexes should work")
@with_app_context
def test_gridding_a_button(app, window):
    for index, widget in enumerate([SimpleButton(window), SimpleMegaWidget(window)]):
        widget.grid(col=index, margin=(1, 2, 3, 4), align=(None, Align.Stretch))
        assert widget.grid.location == (0, index)
        assert widget.grid.row == 0
        assert widget.grid.col == index
        assert widget.grid.margin == (1, 2, 3, 4)
        assert widget.grid.align == (Align.Center, Align.Stretch)
        assert window.grid.size == (index + 1, 1)
