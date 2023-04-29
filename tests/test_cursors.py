import tukaan
from tests.base import with_app_context
from tukaan.enums import Cursor


@with_app_context
def test_cursor_convert(app, window):
    button = tukaan.Label(window, cursor=Cursor.Blank)
    assert button.cursor is Cursor.Blank

    for cursor in Cursor:
        button.cursor = cursor
        assert button.cursor == cursor


@with_app_context
def test_default_cursors(app, window):
    button = tukaan.Button(window)
    assert button.cursor is Cursor.Arrow

    textbox = tukaan.TextBox(window)
    assert textbox.cursor is Cursor.Text
