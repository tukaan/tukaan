import tukaan
from tests.base import with_app_context
from tukaan.enums import Cursor, LegacyX11Cursor


@with_app_context
def test_cursor_convert(app, window):
    button = tukaan.Label(window, cursor=Cursor.Blank)
    assert button.cursor is Cursor.Blank

    for cursor in Cursor:
        button.cursor = cursor
        assert button.cursor == cursor

    for cursor in LegacyX11Cursor:
        button.cursor = cursor
        assert button.cursor == cursor

def test_legacy_x11_cursor_naming():
    for cursor in LegacyX11Cursor:
        if cursor.name == "X":
            continue
        assert cursor.name.lower() == cursor.value.replace("_", "")

@with_app_context
def test_default_cursors(app, window):
    button = tukaan.Button(window)
    assert button.cursor is Cursor.Arrow

    textbox = tukaan.TextBox(window)
    assert textbox.cursor is Cursor.Text
