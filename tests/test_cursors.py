import sys
from pathlib import Path

import pytest

import tukaan
from tests.base import TESTS_DIRECTORY, with_app_context
from tukaan import CursorFile
from tukaan.enums import Cursor, LegacyX11Cursor


@with_app_context
def test_cursor_convert(app, window):
    label = tukaan.Label(window, cursor=Cursor.Blank)
    assert label.cursor is Cursor.Blank

    for cursor in Cursor:
        label.cursor = cursor
        assert label.cursor == cursor

    for cursor in LegacyX11Cursor:
        label.cursor = cursor
        assert label.cursor == cursor


def test_legacy_x11_cursor_naming():
    for cursor in LegacyX11Cursor:
        if cursor.name == "X":
            continue
        assert cursor.name.lower() == cursor.value.replace("_", "")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only cursor loading thingy")
@with_app_context
def test_windows_cursor_file(app, window):
    label = tukaan.Label(window, cursor=CursorFile(TESTS_DIRECTORY / "watch_cursor.ani"))
    assert label.cursor == CursorFile(TESTS_DIRECTORY / "watch_cursor.ani")
    assert label.cursor._name.startswith("@")
    assert label.cursor._name.endswith("watch_cursor.ani")

    with pytest.raises(ValueError):
        CursorFile(Path("./foo.png"))


@pytest.mark.skipif(sys.platform != "linux", reason="Xcursor is Linux only")
@with_app_context
def test_xcursor(app, window):
    label = tukaan.Label(window, cursor=CursorFile(TESTS_DIRECTORY / "watch_cursor"))
    assert label.cursor == CursorFile(TESTS_DIRECTORY / "watch_cursor")


@with_app_context
def test_default_cursors(app, window):
    button = tukaan.Button(window)
    assert button.cursor is Cursor.Arrow

    textbox = tukaan.TextBox(window)
    assert textbox.cursor is Cursor.Text
