import sys

import pytest

from tests.base import with_app_context
from tukaan.enums import WindowType, WindowState


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
