from pathlib import Path

import pytest

import tukaan
from tests.base import update, with_app_context


@with_app_context
def test_checkbox_text(app, window):
    check1 = tukaan.CheckBox(window)
    check2 = tukaan.CheckBox(window, text="Text")

    assert check1.text == ""
    assert check2.text == "Text"
    check1.text = check2.text
    assert check1.text == "Text"


@with_app_context
def test_checkbox_focus(app, window):
    check = tukaan.CheckBox(window, focusable=True)
    check.grid()

    tukaan._tcl.Tcl.call(None, "focus", check)
    update()

    assert tukaan._tcl.Tcl.call(str, "focus") == check._name
    check.focusable = False

    tukaan._tcl.Tcl.call(None, "focus", ".")

    assert tukaan._tcl.Tcl.call(str, "focus") == "."
