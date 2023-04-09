import sys
from pathlib import Path

import pytest

import tukaan
from tests.base import with_app_context
from tukaan.events.event_manager import get_event_and_tcl_sequence
from tukaan.events.events import (
    InvalidBindingSequenceError,
    KeyboardEvent,
    MouseEvent,
    ScrollEvent,
    StateEvent,
    VirtualEvent,
    WindowManagerEvent,
)


def test_convert_tukaan_binding_sequences_to_tcl_platform_specific():
    if sys.platform == "linux":
        # Alt
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-a)>") == (KeyboardEvent, "<Mod1-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-Shift-a)>") == (KeyboardEvent, "<Mod1-Shift-KeyPress-A>")
        # Control / Command
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-a)>") == (KeyboardEvent, "<Control-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-Shift-a)>") == (KeyboardEvent, "<Control-Shift-KeyPress-A>")
        # NumLock
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-a)>") == (KeyboardEvent, "<Mod2-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-Shift-a)>") == (KeyboardEvent, "<Mod2-Shift-KeyPress-A>")
        # AltGr
        assert get_event_and_tcl_sequence("<AltGr-MouseDown:Left>") == (MouseEvent, "<Mod5-ButtonPress-1>")
    elif sys.platform == "darwin":
        # Alt
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-a)>") == (KeyboardEvent, "<Mod2-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-Shift-a)>") == (KeyboardEvent, "<Mod2-Shift-KeyPress-A>")
        # Control / Command
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-a)>") == (KeyboardEvent, "<Mod1-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-Shift-a)>") == (KeyboardEvent, "<Mod1-Shift-KeyPress-A>")
        # NumLock
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-a)>") == (KeyboardEvent, None)
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-Shift-a)>") == (KeyboardEvent, None)
        # AltGr
        assert get_event_and_tcl_sequence("<AltGr-MouseDown:Left>") == (MouseEvent, None)
    elif sys.platform == "win32":
        # Alt
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-a)>") == (KeyboardEvent, "<Mod2-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Alt/Opt-Shift-a)>") == (KeyboardEvent, "<Mod2-Shift-KeyPress-A>")
        # Control / Command
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-a)>") == (KeyboardEvent, "<Control-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(Ctrl/Cmd-Shift-a)>") == (KeyboardEvent, "<Control-Shift-KeyPress-A>")
        # NumLock
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-a)>") == (KeyboardEvent, "<Mod1-KeyPress-a>")
        assert get_event_and_tcl_sequence("<KeyDown:(NumLock-Shift-a)>") == (KeyboardEvent, "<Mod1-Shift-KeyPress-A>")
        # AltGr
        assert get_event_and_tcl_sequence("<AltGr-MouseDown:Left>") == (MouseEvent, "<Control-Alt-ButtonPress-1>")

    if sys.platform == "linux":
        assert get_event_and_tcl_sequence("<KeyDown:(Menu)>") == (KeyboardEvent, "<KeyPress-Menu>")
        assert get_event_and_tcl_sequence("<KeyDown:(Control-Shift-Menu)>") == (KeyboardEvent, "<Control-Shift-KeyPress-Menu>")
    elif sys.platform == "win32":
        assert get_event_and_tcl_sequence("<KeyDown:(Menu)>") == (KeyboardEvent, "<KeyPress-App>")
        assert get_event_and_tcl_sequence("<KeyDown:(Control-Shift-Menu)>") == (KeyboardEvent, "<Control-Shift-KeyPress-App>")

    if sys.platform == "linux":
        assert get_event_and_tcl_sequence("<Wheel:Up>") == (ScrollEvent, "<Button-4>")
        assert get_event_and_tcl_sequence("<Wheel:Down>") == (ScrollEvent, "<Button-5>")
        assert get_event_and_tcl_sequence("<Control-Wheel:Up>") == (ScrollEvent, "<Control-Button-4>")
    else:
        with pytest.raises(InvalidBindingSequenceError):
            get_event_and_tcl_sequence("<Wheel:Up>")
        assert get_event_and_tcl_sequence("<MouseWheel>") == (ScrollEvent, "<MouseWheel>")

    if sys.platform == "linux":
        assert get_event_and_tcl_sequence("<KeyDown:(Shift-Tab)>") == (KeyboardEvent, "<KeyPress-ISO_Left_Tab>")
    else:
        assert get_event_and_tcl_sequence("<KeyDown:(Shift-Tab)>") == (KeyboardEvent, "<Shift-KeyPress-Tab>")


def test_convert_tukaan_keyboard_binding_sequences_to_tcl():
    assert get_event_and_tcl_sequence("<KeyDown:Any>") == (KeyboardEvent, "<KeyPress>")
    assert get_event_and_tcl_sequence("<KeyDown:(a)>") == (KeyboardEvent, "<KeyPress-a>")
    assert get_event_and_tcl_sequence("<KeyDown:(A)>") == (KeyboardEvent, "<KeyPress-A>")
    assert get_event_and_tcl_sequence("<KeyDown:(Shift-a)>") == (KeyboardEvent, "<Shift-KeyPress-A>")
    assert get_event_and_tcl_sequence("<KeyDown:(Shift-A)>") == (KeyboardEvent, "<Shift-KeyPress-A>")
    assert get_event_and_tcl_sequence("<KeyDown:(Control-a)>") == (KeyboardEvent, "<Control-KeyPress-a>")
    assert get_event_and_tcl_sequence("<KeyDown:(Control-A)>") == (KeyboardEvent, "<Control-KeyPress-A>")
    assert get_event_and_tcl_sequence("<KeyDown:(Control-Shift-a)>") == (KeyboardEvent, "<Control-Shift-KeyPress-A>")
    assert get_event_and_tcl_sequence("<KeyDown:(CapsLock-b)>") == (KeyboardEvent, "<Lock-KeyPress-B>")
    assert get_event_and_tcl_sequence("<KeyDown:(CapsLock-B)>") == (KeyboardEvent, "<Lock-KeyPress-B>")
    assert get_event_and_tcl_sequence("<KeyDown:(colon)>") == (KeyboardEvent, "<KeyPress-colon>")
    assert get_event_and_tcl_sequence("<KeyDown:(PageDown)>") == (KeyboardEvent, "<KeyPress-Next>")
    assert get_event_and_tcl_sequence("<KeyDown:(PrintScreen)>") == (KeyboardEvent, "<KeyPress-Print>")
    assert get_event_and_tcl_sequence("<KeyDown:(Shift-Enter)>") == (KeyboardEvent, "<Shift-KeyPress-Return>")

    with pytest.raises(InvalidBindingSequenceError):
        get_event_and_tcl_sequence("<KeyDown:(AltGr-a)>")


@with_app_context
def test_event_aliases_assign_and_unassign(app, window):
    assert app.event_aliases["<<MyEvent>>"] is None

    app.event_aliases.assign("<<MyEvent>>", ["<KeyDown:(Control-a)>", "<MouseDown:Left>"])
    assert app.event_aliases["<<MyEvent>>"] == ["<KeyDown:(Control-a)>", "<MouseDown:Left>"]

    app.event_aliases.unassign("<<MyEvent>>", ["<KeyDown:(Control-a)>"])
    assert app.event_aliases["<<MyEvent>>"] == ["<MouseDown:Left>"]

    del app.event_aliases["<<MyEvent>>"]
    assert app.event_aliases["<<MyEvent>>"] is None


@with_app_context
def test_generating_virtual_events(app, window):
    stuff = []
    handler = lambda: stuff.append("foo")

    label = tukaan.Label(window)
    label.bind("<<MyEvent>>", handler)

    label.generate_event("<<MyEvent>>")
    assert "foo" in stuff

    dummy_object = object()

    def handler(event):
        stuff.append("foo")
        assert event.data is dummy_object

    label.bind("<<MyEvent>>", handler, overwrite=True, send_event=True)

    label.generate_event("<<MyEvent>>", data=dummy_object)
    assert stuff == ["foo", "foo"]