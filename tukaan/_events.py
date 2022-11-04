from __future__ import annotations

import re
from functools import partial
from typing import Any, Callable, Union
from uuid import uuid4

from tukaan._collect import _widgets
from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan._utils import reversed_dict
from tukaan.enums import EventQueue

from ._keysyms import keysym_aliases, reversed_keysym_aliases

if Platform.os == "macOS":
    BUTTON_NUMS = {"left": 1, "middle": 3, "right": 2}
    ACCEL_MODIFIER_ORDER = {"Option": "⌥", "Shift": "⇧", "Control": "⌃", "Command": "⌘"}
    MODIFIER_MAP = {
        "Ctrl_Ctrl": "Control",
        "Ctrl_Cmd": "Command",
        "Alt_Opt": "Option",
        "Shift": "Shift",
    }
    SHORTCUT_SEP = ""
else:
    BUTTON_NUMS = {"left": 1, "middle": 2, "right": 3}
    ACCEL_MODIFIER_ORDER = {"Control": "Ctrl", "Control": "Ctrl", "Alt": "Alt", "Shift": "Shift"}
    MODIFIER_MAP = {
        "Ctrl_Ctrl": "Control",
        "Ctrl_Cmd": "Control",
        "Alt_Opt": "Alt",
        "Shift": "Shift",
    }
    SHORTCUT_SEP = "+"

MODIFIERS = {
    1 << 12: "MouseWheel:Down",
    1 << 11: "MouseWheel:Up",
    1 << 10: "MouseButton:Right",
    1 << 9: "MouseButton:Middle",
    1 << 8: "MouseButton:Left",
    1 << 7: "Mod5",
    1 << 6: "Mod4",
    1 << 5: "Mod3",
    1 << 4: "Mod2",
    1 << 3: "Mod1",
    1 << 2: "Control",
    1 << 1: "CapsLock",
    1 << 0: "Shift",
}


class DataContainer:
    _container_dict: dict[str, Any] = {}

    def add(self, value: object) -> str:
        key = str(uuid4())
        self._container_dict[key] = value
        return key

    def pop(self, key: str) -> Any:
        return self._container_dict.pop(key, None)

    def __getitem__(self, key: str) -> Any:
        return self._container_dict[key]


_virtual_event_data_container = DataContainer()


class Event:
    _sequence_aliases: dict[str, str]
    _ignored_values: tuple[object, ...]
    _relevant_attrs: tuple[str]
    _result: str | bool = True
    _substitutions: dict[str, tuple[str, type]] = {
        "button": ("%b", int),
        "modifiers": ("%s", int),
        "keycode": ("%k", int),
        "rel_x": (r"%x", int),
        "rel_y": (r"%y", int),
        "char": ("%A", str),
        "delta": ("%D", float),
        "keysymbol": ("%K", str),
        "widget": (r"%W", str),
        "abs_x": (r"%X", int),
        "abs_y": (r"%Y", int),
    }
    _order: tuple[str, ...] = tuple(_substitutions.keys())
    # FIXME: _order must be updated when subclass overwrites _substitutions, this makes the code fragile
    # Tukaan requires python 3.7+, so we don't need an OrderedDict

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self._substitutions[item][1], value)
            else:
                value = None

            setattr(self, item, value)

    def __repr__(self) -> str:
        pairs = []

        for name in self._relevant_attrs:
            value = getattr(self, name)
            if value not in self._ignored_values:
                pairs.append(f"{name}={value!r}")

        return f"<{type(self).__name__}: {', '.join(pairs)}>"

    @staticmethod
    def _get_event_class_for_sequence(sequence: str) -> type[Event]:
        for klass in (KeyboardEvent, MouseEvent, ScrollEvent, StateEvent, VirtualEvent):
            if klass._match(sequence):
                return klass

        raise ValueError(f"invalid binding sequence: {sequence}")

    def _get_modifiers(self, value: int) -> set[str]:
        result = []

        for modifier_value in MODIFIERS:
            if value >= modifier_value:
                value -= modifier_value
                result.append(MODIFIERS[modifier_value])

        return set(result)

    @classmethod
    def _match(cls, sequence: str) -> bool:
        return sequence in cls._sequence_aliases

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return cls._sequence_aliases[sequence]

    def abort(self) -> bool:
        self._result = False
        return self._result


class KeyboardEvent(Event):
    _ignored_values = (None, "", "??", -1, 0, (), set())
    _relevant_attrs = ("char", "modifiers", "keysymbol", "keycode")
    _regex = r"<Key(Down|Up):\((.*?)\)>"

    _sequence_aliases = {
        "<KeyDown:Any>": "<KeyPress>",
        "<KeyDown>": "<KeyPress>",
        "<KeyUp:Any>": "<KeyRelease>",
        "<KeyUp>": "<KeyRelease>",
    }

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self._substitutions[item][1], value)
            else:
                value = None

            if item == "keysymbol" and value in keysym_aliases:
                value = keysym_aliases[value]
            elif item == "modifiers":
                value = self._get_modifiers(value)

            setattr(self, item, value)

    @classmethod
    def _match(cls, sequence: str) -> bool:
        return sequence in cls._sequence_aliases or bool(re.match(cls._regex, sequence))

    @classmethod
    def _parse(cls, sequence: str) -> str:
        up_or_down = {"Down": "Press", "Up": "Release"}

        if sequence in cls._sequence_aliases:
            return cls._sequence_aliases[sequence]
        elif re.match(cls._regex, sequence):
            search = re.search(cls._regex, sequence)
            assert search is not None  # mypy

            keys = search[2].split("-")
            key = keys[-1]
            if key in reversed_keysym_aliases:
                key = reversed_keysym_aliases.get(key)
            elif key == "Any":
                key = ""

            modifier_keys = keys[:-1]
            for mod in modifier_keys:
                if mod in reversed_keysym_aliases:
                    modifier_keys.remove(mod)
                    modifier_keys.append(reversed_keysym_aliases[mod])

            if "Shift" in modifier_keys:
                if len(key) == 1:
                    key = key.upper()
                elif key == "Tab" and Tcl.windowing_system == "x11":
                    modifier_keys.remove("Shift")
                    key = "ISO_Left_Tab"

            modifiers = "-".join(modifier_keys) + ("-" if modifier_keys else "")

            return f"<{modifiers}Key{up_or_down[search[1]]}{('-' + key) if key else ''}>"

        raise Exception("this shouldn't happen")


class MouseEvent(Event):
    _ignored_values = (None, "??", set())
    _relevant_attrs = ("button", "modifiers", "abs_x", "abs_y", "rel_x", "rel_y")

    _sequence_aliases = {
        # button press
        "<MouseDown:Any:Double>": "<Double-ButtonPress>",
        "<MouseDown:Any:Triple>": "<Triple-ButtonPress>",
        "<MouseDown:Any:Triple>": "<Quadruple-ButtonPress>",
        "<MouseDown:Any>": "<ButtonPress>",
        "<MouseDown:Left:Double>": "<Double-ButtonPress-{left}>",
        "<MouseDown:Left:Triple>": "<Triple-ButtonPress-{left}>",
        "<MouseDown:Left:Quadruple>": "<Quadruple-ButtonPress-{left}>",
        "<MouseDown:Left>": "<ButtonPress-{left}>",
        "<MouseDown:Middle:Double>": "<Double-ButtonPress-{middle}>",
        "<MouseDown:Middle:Triple>": "<Triple-ButtonPress-{middle}>",
        "<MouseDown:Middle:Quadruple>": "<Quadruple-ButtonPress-{middle}>",
        "<MouseDown:Middle>": "<ButtonPress-{middle}>",
        "<MouseDown:Right:Double>": "<Double-ButtonPress-{right}>",
        "<MouseDown:Right:Triple>": "<Triple-ButtonPress-{right}>",
        "<MouseDown:Right:Quadruple>": "<Quadruple-ButtonPress-{right}>",
        "<MouseDown:Right>": "<ButtonPress-{right}>",
        "<MouseDown>": "<ButtonPress>",
        # drag
        "<MouseDrag:Left>": "<Button{left}-Motion>",
        "<MouseDrag:Middle>": "<Button{middle}-Motion>",
        "<MouseDrag:Right>": "<Button{right}-Motion>",
        # button release
        "<MouseUp:Any>": "<ButtonRelease>",
        "<MouseUp:Left>": "<ButtonRelease-{left}>",
        "<MouseUp:Middle>": "<ButtonRelease-{middle}>",
        "<MouseUp:Right>": "<ButtonRelease-{right}>",
        "<MouseUp>": "<ButtonRelease>",
        # mouse motion
        "<MouseEnter>": "<Enter>",
        "<MouseLeave>": "<Leave>",
        "<MouseMotion>": "<Motion>",
    }

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self._substitutions[item][1], value)
            else:
                value = None

            if value and item == "button":
                value = reversed_dict(BUTTON_NUMS).get(value)
            elif item == "modifiers":
                value = self._get_modifiers(value)

            setattr(self, item, value)

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return cls._sequence_aliases[sequence].format(**BUTTON_NUMS)


class ScrollEvent(Event):
    _ignored_values = (None, "??", set())
    _relevant_attrs = ("delta", "modifiers")
    _sequence_aliases = {}

    def __init__(self, *args) -> None:
        if Tcl.windowing_system == "x11":
            num = Tcl.from_(int, args[self._order.index("button")])
            self.delta = -1 if num == 4 else 1
        else:
            self.delta = Tcl.from_(int, args[self._order.index("delta")])

        self.modifiers = self._get_modifiers(Tcl.from_(int, args[self._order.index("modifiers")]))

    @classmethod
    def _match(cls, sequence: str) -> bool:
        return any(x in sequence for x in {"MouseWheel", "Button-4", "Button-5"})

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return sequence


class StateEvent(Event):
    _ignored_values = (None, "??", set())
    _relevant_attrs = ()
    _sequence_aliases = {
        "<FocusIn>": "<FocusIn>",
        "<FocusOut>": "<FocusOut>",
        "<AltUnderline>": "<<AltUnderlined>>",
    }


class VirtualEvent(Event):
    _substitutions = {"data": ("%d", int), "widget": ("%W", str)}
    _order = tuple(_substitutions.keys())
    _sequence_aliases = {}

    def __init__(self, *args) -> None:
        data_key = Tcl.from_(str, args[0])

        self.data = _virtual_event_data_container.pop(data_key) if data_key else None

    def __repr__(self) -> str:
        plus_str = "" if self.data is None else f"; data={self.data!r}"
        return f"<VirtualEvent: {self.sequence}{plus_str}>"

    @classmethod
    def _match(cls, sequence: str) -> bool:
        return sequence.startswith("<<") and sequence.endswith(">>") and len(sequence) > 4

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return sequence


_BindCallback = Union[
    Callable[[], Union[str, bool, None]], Callable[[Event], Union[str, bool, None]]
]


def binding_wrapper(
    widget, sequence: str, func: _BindCallback, event: type[Event], send: bool, *args: str
) -> str | bool | None:
    if (
        Tcl.windowing_system == "x11"
        and event is MouseEvent
        and int(args[event._order.index("button")]) > 3
    ):
        # Don't execute callback if the binding was <Mouse(Down|Up):Any>,
        # and the button number is 4 or 5 (mouse wheel)
        return

    if not send:
        return func()

    sent_event = event(*args)
    sent_event.sequence = sequence
    sent_event.widget = _widgets.get(args[event._order.index("widget")])
    result = func(sent_event)

    if result is not None:
        return result

    return sent_event._result


class BindingsMixin:
    _name: str

    def bind(
        self,
        sequence: str,
        callback: _BindCallback | None,
        *,
        overwrite: bool = False,
        send: bool = False,
    ) -> None:
        if isinstance(sequence, KeySeq):
            sequence = sequence.event_sequence

        if "MouseWheel" in sequence and Tcl.windowing_system == "x11":
            self.bind(
                sequence.replace("MouseWheel", "Button-4"), callback, overwrite=overwrite, send=send
            )
            self.bind(
                sequence.replace("MouseWheel", "Button-5"), callback, overwrite=overwrite, send=send
            )
            return
        elif "Menu" in sequence and Platform.os == "Windows":
            sequence = sequence.replace("Menu", "App")

        event = Event._get_event_class_for_sequence(sequence)

        if callable(callback):
            cmd = Tcl.to(partial(binding_wrapper, self, sequence, callback, event, send))
            subst_str = " ".join(item[0] for item in event._substitutions.values())
            script_str = f"{'' if overwrite else '+'} if {{[{cmd} {subst_str}] == 0}} break"
        else:
            script_str = ""

        if hasattr(self, "_wm_path"):
            # can't import ToplevelBase here
            name = self._wm_path
        else:
            name = self._name

        Tcl.call(None, "bind", name, event._parse(sequence), script_str)

    def unbind(self, sequence: str) -> None:
        self.bind(sequence, None)

    def generate_event(self, sequence: str, data: object = None, queue: EventQueue = None) -> None:
        if not VirtualEvent._match(sequence):
            # I don't want people to generate physical event with this
            # maybe somewhere else
            raise Exception("can only generate virtual events")

        if data is None:
            key = None
        else:
            key = _virtual_event_data_container.add(data)

        if hasattr(self, "_wm_path"):
            name = self._wm_path
        else:
            name = self._name

        Tcl.call(None, "event", "generate", name, sequence, *Tcl.to_tcl_args(data=key, when=queue))


class KeySeq:
    _wrong_modifiers = {
        "Alt": "'Alt_Opt'",
        "Command": "'Ctrl_Cmd'",
        "Control": "'Ctrl_Cmd' or 'Ctrl_Ctrl'",
    }

    def __init__(self, *args: str) -> None:
        seq = []
        non_mod_key = ""

        for key in list(args):
            if key in self._wrong_modifiers:
                raise ValueError(
                    f"wrong modifier key: {key!r}. Use {self._wrong_modifiers[key]} instead."
                )
            elif " " in key:
                raise ValueError(f"invalid key: {key!r}")

            if key in MODIFIER_MAP:
                seq.append(MODIFIER_MAP.get(key))
            else:
                non_mod_key = key

            seq = list(set(seq))  # just to remove duplicates

        if not non_mod_key:
            raise Exception("invalid key sequence")

        seq.append(non_mod_key)
        self._sequence = seq

    @property
    def event_sequence(self) -> str:
        return f"<KeyDown:({'-'.join(self._sequence)})>"

    @property
    def accelerator_sequence(self) -> str:
        non_mod_key = self._sequence[-1]

        result = [sym for name, sym in ACCEL_MODIFIER_ORDER.items() if name in self._sequence]
        result.append(non_mod_key.upper())

        return SHORTCUT_SEP.join(result)

    def __eq__(self, other: object) -> bool:
        return (
            set(self._sequence) == set(other._sequence)
            if isinstance(other, KeySeq)
            else NotImplemented
        )
