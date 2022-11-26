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
def test_checkbox_action(app, window):
    stuff = []
    command = lambda _: stuff.append("foo")

    check = tukaan.CheckBox(window, action=command)

    check.invoke()
    assert "foo" in stuff
    assert check.selected

    check.action = lambda sel: stuff.append(sel)
    check.invoke()
    assert False in stuff


@with_app_context
def test_checkbox_select(app, window):
    variable = tukaan.BoolVar(True)

    check = tukaan.CheckBox(window, target=variable)

    assert check.selected
    check.selected = False
    assert not check.selected
    check.selected = True
    assert check.selected
    check.deselect()
    assert not check.selected
    check.select()
    assert check.selected
    check.toggle()
    assert not check.selected
