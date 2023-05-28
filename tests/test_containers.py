import pytest

from tukaan import Panel, SplitView
from tukaan._base import Widget
from tukaan._tcl import Tcl
from tukaan.enums import Orientation


def test_panel_initialization(root):
    panel = Panel(root, padding=(1, 2, 3, 4))
    assert panel.parent is root
    assert panel.padding == (1, 2, 3, 4)
    panel.padding = (4, 9, 2, 6)
    assert panel.padding == (4, 9, 2, 6)


def test_pane_initialization(root):
    split_view = SplitView(root)
    pane = split_view.create_pane(padding=(1, 2, 3, 4), weight=2)
    assert pane.parent is split_view
    assert pane in split_view.panes
    assert pane in split_view

    assert pane.padding == (1, 2, 3, 4)
    pane.padding = (4, 9, 2, 6)
    assert pane.padding == (4, 9, 2, 6)

    assert pane.weight == 2
    pane.weight = 7
    assert pane.weight == 7


def test_pane_append(root):
    split_view = SplitView(root)
    pane = split_view.create_pane(auto_append=False)
    pane.append()
    assert pane in split_view.panes
    assert pane in split_view


def test_pane_move(root):
    split_view = SplitView(root)
    pane1 = split_view.create_pane()
    pane2 = split_view.create_pane()
    pane3 = split_view.create_pane()
    assert split_view.panes == [pane1, pane2, pane3]

    pane2.move(0)
    assert split_view.panes == [pane2, pane1, pane3]

    pane1.append()
    assert split_view.panes == [pane2, pane3, pane1]

    with pytest.raises(ValueError):
        pane3.move(-1)


def test_pane_remove(root):
    split_view = SplitView(root)
    pane = split_view.create_pane()
    pane.remove()
    assert pane not in split_view.panes
    assert pane not in split_view


def test_pane_weight_property(root):
    split_view = SplitView(root)
    pane = split_view.create_pane(weight=2)
    assert pane.weight == 2
    pane.weight = 3
    assert pane.weight == 3


def test_split_view_initialization(root):
    split_view = SplitView(root, orientation=Orientation.Horizontal)
    assert split_view.parent is root
    assert split_view.orientation is Orientation.Horizontal
    with pytest.raises(AttributeError):
        split_view.orientation = Orientation.Vertical


def test_split_view_length(root):
    split_view = SplitView(root)
    for i in range(10):
        split_view.create_pane()
    assert len(split_view) == 10


def test_split_view_iteration(root):
    split_view = SplitView(root)
    pane1 = split_view.create_pane()
    pane2 = split_view.create_pane()
    panes = [pane for pane in split_view]
    assert panes == [pane1, pane2]


def test_split_view_getitem(root):
    split_view = SplitView(root)
    pane1 = split_view.create_pane()
    pane2 = split_view.create_pane()
    assert split_view[0] is pane1
    assert split_view[1] is pane2


def test_split_view_lock_panes(root):
    split_view = SplitView(root)
    split_view.lock_panes()
    assert Tcl.call((Widget, str), "bindtags", split_view) == (split_view, ".", "all")

    split_view.unlock_panes()
    assert Tcl.call((Widget, str), "bindtags", split_view) == (
        split_view,
        split_view._tk_class,
        ".",
        "all",
    )
