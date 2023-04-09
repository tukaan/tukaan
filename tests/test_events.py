from pathlib import Path

import tukaan
from tests.base import with_app_context


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