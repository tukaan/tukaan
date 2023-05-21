import sys

import pytest

from tukaan.enums import Resizable, WindowState, WindowType


@pytest.mark.xfail
def test_window_geometry(root):
    # This test succeds if I put `test_window_size_increment` down there, but it's weird
    assert isinstance(root.x, int)
    assert isinstance(root.y, int)
    assert isinstance(root.width, int)
    assert isinstance(root.height, int)

    initial_y = root.y
    root.x = 100
    assert root.x == 100
    assert root.y == initial_y
    root.y = 150
    assert root.y == 150
    assert root.x == 100
    assert root.position == (100, 150)

    initial_height = root.height
    root.width = 200
    assert root.width == 200
    assert root.height == initial_height
    root.height = 250
    assert root.width == 200
    assert root.height == 250  # this fails randomly ://
    assert root.size == (200, 250)


def test_window_min_max_size(root):
    assert isinstance(root.min_size, tuple)
    assert isinstance(root.max_size, tuple)

    root.min_size = 200
    assert root.min_size == (200, 200)
    root.min_size = (100, 100)
    assert root.min_size == (100, 100)

    root.max_size = 800
    assert root.max_size == (800, 800)
    root.max_size = 400
    assert root.max_size == (400, 400)


def test_window_resizable(root):
    assert isinstance(root.resizable, Resizable)

    root.resizable = Resizable.Not
    assert root.resizable == Resizable.Not
    root.resizable = Resizable.Vertical
    assert root.resizable == Resizable.Vertical
    root.resizable = Resizable.Horizontal
    assert root.resizable == Resizable.Horizontal
    root.resizable = Resizable.Both
    assert root.resizable == Resizable.Both


def test_window_size_increment(root):
    assert isinstance(root.size_increment, tuple)

    root.size_increment = 20
    assert root.size_increment == (20, 20)
    root.size_increment = (10, 10)
    assert root.size_increment == (10, 10)


def test_main_window_class_name(app, root):
    assert root.class_name == app.name.capitalize().replace(" ", "_") == "Test_app"


def test_main_window_id_and_hwnd(app, root):
    # Serious test lol
    assert isinstance(root.id, int)
    assert isinstance(root.hwnd, int)


def test_window_title(root):
    assert root.title == "Test window"
    root.title = "Something really cool"
    assert root.title == "Something really cool"
    root.title = None
    assert root.title == ""


@pytest.mark.skip(reason="fails during tests")
def test_window_always_on_top(root):
    root.always_on_top = True
    assert root.always_on_top
    root.always_on_top = False
    assert not root.always_on_top


def test_window_opacity(root):
    assert root.opacity == 1.0
    root.opacity = 0.8
    assert root.opacity == 0.8
    root.opacity = 0.6789
    assert root.opacity == 0.6789


def test_window_state(root):
    initial_window_state = root.state
    assert isinstance(root.state, WindowState)
    root.minimize()
    assert root.state is WindowState.Minimized
    root.restore()
    assert root.state is initial_window_state
    root.hide()
    assert root.state is WindowState.Hidden
    root.unhide()
    assert root.state is initial_window_state
    # other stuff fails randomly on my system


@pytest.mark.skipif(sys.platform != "linux", reason="window types are available on X11 only")
def test_window_type_x11(root):
    assert root.type is WindowType.Normal
    root.type = WindowType.Dialog
    assert root.type is WindowType.Dialog
    root.type = WindowType.Utility
    assert root.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only toolwindow feature")
def test_window_type_windows(root):
    assert root.type is WindowType.Normal
    root.type = WindowType.Utility
    assert root.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only 'dirty' close button feature")
def test_window_dirty(root):
    assert not root.dirty
    root.dirty = True
    assert root.dirty
    root.dirty = False
    assert not root.dirty
