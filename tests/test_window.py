from pathlib import Path

import tukaan
from tests.base import with_app_context


@with_app_context
def test_window_icon_is_initially_None(app, window):
    assert window.icon is None


@with_app_context
def test_window_icon_icon_path(app, window):
    icon_path = Path(__file__).resolve().parent / "foo.png"
    window.icon = icon_path
    assert isinstance(window.icon, tukaan.Icon)


@with_app_context
def test_window_icon_icon_object(app, window):
    icon = tukaan.Icon(Path(__file__).resolve().parent / "foo.png")
    window.icon = icon
    assert window.icon is icon
