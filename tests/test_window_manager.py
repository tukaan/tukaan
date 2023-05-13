import sys

import pytest

from tests.base import with_app_context
from tukaan.enums import WindowType


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


@with_app_context
def test_window_opacity(app, window):
    assert window.opacity == 1.0
    window.opacity = 0.8
    assert window.opacity == 0.8
    window.opacity = 0.6789
    assert window.opacity == 0.6789


@pytest.mark.skipif(sys.platform != "linux", reason="window types are available on X11 only")
@with_app_context
def test_window_type_x11(app, window):
    assert window.type is WindowType.Normal
    window.type = WindowType.Dialog
    assert window.type is WindowType.Dialog
    window.type = WindowType.Utility
    assert window.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "win32", reason="testing Windows toolwindow feature")
@with_app_context
def test_window_type_windows(app, window):
    assert window.type is WindowType.Normal
    window.type = WindowType.Utility
    assert window.type is WindowType.Utility


@pytest.mark.skipif(sys.platform != "darwin", reason="testing macOS 'dirty' close button feature")
@with_app_context
def test_window_dirty(app, window):
    assert not window.dirty
    window.dirty = True
    assert window.dirty
    window.dirty = False
    assert not window.dirty
