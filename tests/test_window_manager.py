import sys

import pytest

from tests.base import with_app_context
from tukaan.enums import Resizable, WindowState, WindowType


@pytest.mark.xfail
@with_app_context
def test_window_geometry(app, window):
    # This test succeds if I put `test_window_size_increment` down there, but it's weird
    assert isinstance(window.x, int)
    assert isinstance(window.y, int)
    assert isinstance(window.width, int)
    assert isinstance(window.height, int)

    initial_y = window.y
    window.x = 100
    assert window.x == 100
    assert window.y == initial_y
    window.y = 150
    assert window.y == 150
    assert window.x == 100
    assert window.position == (100, 150)

    initial_height = window.height
    window.width = 200
    assert window.width == 200
    assert window.height == initial_height
    window.height = 250
    assert window.width == 200
    assert window.height == 250  # this fails randomly ://
    assert window.size == (200, 250)


@with_app_context
def test_window_min_max_size(app, window):
    assert isinstance(window.min_size, tuple)
    assert isinstance(window.max_size, tuple)

    window.min_size = 200
    assert window.min_size == (200, 200)
    window.min_size = (100, 100)
    assert window.min_size == (100, 100)

    window.max_size = 800
    assert window.max_size == (800, 800)
    window.max_size = 400
    assert window.max_size == (400, 400)


@with_app_context
def test_window_resizable(app, window):
    assert isinstance(window.resizable, Resizable)

    window.resizable = Resizable.Not
    assert window.resizable == Resizable.Not
    window.resizable = Resizable.Vertical
    assert window.resizable == Resizable.Vertical
    window.resizable = Resizable.Horizontal
    assert window.resizable == Resizable.Horizontal
    window.resizable = Resizable.Both
    assert window.resizable == Resizable.Both


@with_app_context
def test_window_size_increment(app, window):
    assert isinstance(window.size_increment, tuple)

    window.size_increment = 20
    assert window.size_increment == (20, 20)
    window.size_increment = (10, 10)
    assert window.size_increment == (10, 10)


@with_app_context
def test_main_window_class_name(app, window):
    assert window.class_name == app.name.capitalize().replace(" ", "_") == "Test_app"


@with_app_context
def test_main_window_id_and_hwnd(app, window):
    # Serious test lol
    assert isinstance(window.id, int)
    assert isinstance(window.hwnd, int)


@with_app_context
def test_window_title(app, window):
    assert window.title == "Test window"
    window.title = "Something really cool"
    assert window.title == "Something really cool"
    window.title = None
    assert window.title == ""


@pytest.mark.skip(reason="fails during tests")
@with_app_context
def test_window_always_on_top(app, window):
    window.always_on_top = True
    assert window.always_on_top
    window.always_on_top = False
    assert not window.always_on_top


@with_app_context
def test_window_opacity(app, window):
    assert window.opacity == 1.0
    window.opacity = 0.8
    assert window.opacity == 0.8
    window.opacity = 0.6789
    assert window.opacity == 0.6789


@with_app_context
def test_window_state(app, window):
    initial_window_state = window.state
    assert isinstance(window.state, WindowState)
    window.minimize()
    assert window.state is WindowState.Minimized
    window.restore()
    assert window.state is initial_window_state
    window.hide()
    assert window.state is WindowState.Hidden
    window.unhide()
    assert window.state is initial_window_state
    # other stuff fails randomly on my system


@pytest.mark.skipif(sys.platform != "linux", reason="window types are available on X11 only")
@with_app_context
def test_window_type_x11(app, window):
    assert window.type is WindowType.Normal
    window.type = WindowType.Dialog
    assert window.type is WindowType.Dialog
    window.type = WindowType.Utility
    assert window.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only toolwindow feature")
@with_app_context
def test_window_type_windows(app, window):
    assert window.type is WindowType.Normal
    window.type = WindowType.Utility
    assert window.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only 'dirty' close button feature")
@with_app_context
def test_window_dirty(app, window):
    assert not window.dirty
    window.dirty = True
    assert window.dirty
    window.dirty = False
    assert not window.dirty
