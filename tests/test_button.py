from pathlib import Path

import pytest

import tukaan
from tests.base import update, with_app_context


@with_app_context
def test_button_text_and_action(app, window):
    stuff = []
    command = lambda: stuff.append("foo")

    button1 = tukaan.Button(window)
    button2 = tukaan.Button(window, text="Text")
    button3 = tukaan.Button(window, text="Text", action=command)

    assert button1.text == ""
    assert button2.text == "Text"
    assert button2.text == button3.text

    assert button2.action is None
    assert button3.action is command

    button2.action = button3.action
    assert button2.action is command

    result = button2.invoke()
    assert result is None
    assert "foo" in stuff

    result = button3.invoke()
    assert result is None
    assert stuff == ["foo", "foo"]


@pytest.mark.skip(reason="`button.image` isn't implemented for some reason")
@with_app_context
def test_button_image(app, window):
    icon = tukaan.Icon(file=Path(__file__).resolve().parent / "foo.png")

    button = tukaan.Button(window, image=icon)

    assert button.image is icon
    button.image = None
    assert button.image is None
    button.image = icon
    assert button.image is icon

    assert button.image_pos is tukaan.enums.ImagePosition.Default
    button.image_pos = tukaan.enums.ImagePosition.Left
    assert button.image_pos is tukaan.enums.ImagePosition.Left
    button.image_pos = tukaan.enums.ImagePosition.Default
    assert button.image_pos is tukaan.enums.ImagePosition.Default


@with_app_context
def test_button_focus(app, window):
    button = tukaan.Button(window, focusable=True)
    button.grid()

    tukaan._tcl.Tcl.call(None, "focus", button)
    update()

    assert tukaan._tcl.Tcl.call(str, "focus") == button._name
    button.focusable = False

    tukaan._tcl.Tcl.call(None, "focus", ".")

    assert tukaan._tcl.Tcl.call(str, "focus") == "."


@with_app_context
def test_button_width(app, window):
    button = tukaan.Button(window, text="Text", width=1)

    assert button.width == 1
    button.width = 2
    assert button.width == 2
