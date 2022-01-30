from __future__ import annotations

import re
from functools import partial
from typing import Any, Callable

from ._base import TkWidget
from ._dnd import _DND_BINDING_SUBSTS, DND_SEQUENCES, DnDEvent
from ._utils import create_command, from_tcl, reversed_dict

_BINDING_SUBSTS = (
    ("%b", int, "button_number"),
    ("%c", int, "count"),
    (r"%h", int, "height"),
    ("%k", str, "keycode"),
    (r"%w", int, "width"),
    (r"%x", int, "x"),
    (r"%y", int, "y"),
    ("%A", str, "char"),
    ("%D", float, "delta"),
    ("%K", str, "keysymbol"),
    (r"%W", TkWidget, "widget"),
    (r"%X", int, "rel_x"),
    (r"%Y", int, "rel_y"),
)

_BINDING_ALIASES = {
    "<KeyDown>": "<KeyPress>",
    "<KeyUp>": "<KeyRelease>",
    "<MouseDown:Left>": "<ButtonPress-1>",
    "<MouseDown:Middle>": "<ButtonPress-2>",
    "<MouseDown:Right>": "<ButtonPress-3>",
    "<MouseDown>": "<ButtonPress>",
    "<MouseEnter>": "<Enter>",
    "<MouseLeave>": "<Leave>",
    "<MouseMotion>": "<Motion>",
    "<MouseUp:Left>": "<ButtonRelease-1>",
    "<MouseUp:Middle>": "<ButtonRelease-2>",
    "<MouseUp:Right>": "<ButtonRelease-3>",
    "<MouseUp>": "<ButtonRelease>",
    "<MouseWheelRotate>": "<MouseWheel>",
}

_KEYSYMS = {
    "Space": "space",
    "Backspace": "BackSpace",
    "Enter": "Return",
    "CapsLock": "Caps_Lock",
    "NumLock": "Num_Lock",
    "ScrollLock": "Scroll_Lock",
    "PauseBreak": "Pause",
    "PrintScreen": "Print",
    "PageUp": "Prior",
    "PageDown": "Next",
}


class Event:
    data: Any
    sequence: str

    def __init__(self, func: Callable, data: Any) -> None:
        self.callback = func
        self.data = data

    def __repr__(self) -> str:
        ignored_values = {None, "??", -1, 0}
        relevant_attrs = ("delta", "keysymbol", "keycode", "char")
        pairs = []

        for name in relevant_attrs:
            value = getattr(self, name)
            if value not in ignored_values:
                pairs.append(f"{name}={value!r}")
        if self.data is not None:
            pairs.append(f"data={self.data!r}")

        return f"<Event: {', '.join(sorted(pairs))}>"

    def _set_values(self, *args):
        for (_, type_, attr), string_value in zip(_BINDING_SUBSTS, args):
            if string_value == "??":
                value = None
            else:
                value = from_tcl(type_, string_value)

            if attr == "keysymbol" and value in _KEYSYMS.values():
                value = reversed_dict(_KEYSYMS)[string_value]

            setattr(self, attr, value)


class EventManager:
    def __parse_sequence(self, sequence: str) -> str:
        tcl_sequence = sequence
        regex_str = r"<Key(Down|Up):(.*?)>"

        if sequence in _BINDING_ALIASES:
            tcl_sequence = _BINDING_ALIASES[sequence]
        elif re.match(regex_str, sequence):
            search = re.search(regex_str, sequence)
            assert search is not None  # mypy grrr

            up_or_down = {"Down": "Press", "Up": "Release"}

            thing = search.group(2)
            if thing in _KEYSYMS:
                thing = _KEYSYMS[thing]

            tcl_sequence = f"<Key{up_or_down[search.group(1)]}-{thing}>"  # type: ignore

        return tcl_sequence

    def _call_bind(
        self,
        sequence: tuple[str, ...] | str,
        func: Callable | str,
        overwrite: bool,
        send_event: bool,
        data: Any,
    ) -> None:
        if sequence in DND_SEQUENCES:
            is_dnd = True
        else:
            is_dnd = False

        def _real_func(func: Callable, data: Any, *args):
            if send_event:
                if is_dnd:
                    event = DnDEvent()
                else:
                    event = Event(func, data)

                event._set_values(*args)

                return func(event)
            else:
                return func()

        if callable(func):
            cmd = create_command(partial(_real_func, func, data))

            if is_dnd:
                sequence = DND_SEQUENCES[sequence]

                subst_str = " ".join(subs for subs, *_ in _DND_BINDING_SUBSTS)
                script_str = (
                    f"{'' if overwrite else '+'} {cmd} {subst_str}"  # tcl: {+ command %subst}
                )
            else:
                subst_str = " ".join(subs for subs, *_ in _BINDING_SUBSTS)
                script_str = f"{'' if overwrite else '+'} if {{[{cmd} {subst_str}] == 0}} break"  # tcl: {+ if {[command %subst] == 0} break}
        else:
            script_str = func  # func is "" when unbinding

        self._widget._tcl_call(
            None, "bind", self._widget, self.__parse_sequence(sequence), script_str
        )

    def bind(
        self,
        sequence: str,
        func: Callable,
        overwrite: bool = False,
        send_event: bool = False,
        data=None,
    ) -> None:
        self._call_bind(sequence, func, overwrite, send_event, data)

    def unbind(self, sequence: str):
        self._call_bind(sequence, "", True, False, None)

    def generate_event(self, sequence: str):
        self._widget._tcl_call(None, "event", "generate", self, self.__parse_sequence(sequence))
