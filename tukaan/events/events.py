from __future__ import annotations

import re
from uuid import uuid4
from typing import Any

from tukaan._misc import Mouse
from tukaan._tcl import Tcl
from tukaan._typing import T
from tukaan._utils import reversed_dict
from .keysyms import KEYSYM_ALIASES, REV_KEYSYM_ALIASES

from .constants import (
    BINDING_MODIFIER_MAP,
    BUTTON_NUMS,
    KEYBOARD_MODIFIERS_REGEX,
    MOD_STATE_MAP,
    KEYBOARD_EVENT_REGEX,
)


def get_modifiers(value: int) -> set[str]:
    result = []

    for modifier_value in MOD_STATE_MAP:
        if value >= modifier_value:
            value -= modifier_value
            result.append(MOD_STATE_MAP[modifier_value])

    return set(result)


class InvalidBindingSequenceError(Exception):
    def __init__(self, sequence: str) -> None:
        super().__init__(f"not a valid binding sequence: {sequence}")


class DataContainer:
    # FIXME: alternative from stdlib
    _container_dict: dict[str, Any] = {}

    def add(self, value: object) -> str:
        key = uuid4().hex
        self._container_dict[key] = value
        return key

    def pop(self, key: str) -> Any:
        return self._container_dict.pop(key, None)

    def __getitem__(self, key: str) -> Any:
        return self._container_dict[key]


_virtual_event_data_container = DataContainer()


class Event:
    sequence: str  # set in EventCallback.__call__
    _subclasses: list[type[Event]] = []

    _ignored_values: tuple[object, ...] = (None, "??", set())
    _relevant_attrs: tuple[str, ...] = ()
    _aliases: dict[str, str] = {}
    _subst: dict[str, tuple[str, type]] = {
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

    def __init_subclass__(cls) -> None:
        Event._subclasses.append(cls)

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[tuple(self._subst.keys()).index(item)]
            if value == "??":
                value = None
            else:
                value = Tcl.from_(self._subst[item][1], value)

            setattr(self, item, value)

    def __repr__(self) -> str:
        pairs = []

        for name in self._relevant_attrs:
            value = getattr(self, name)
            if value not in self._ignored_values:
                pairs.append(f"{name}={value!r}")

        return f"<{type(self).__name__}: {', '.join(pairs)}>"

    @classmethod
    def _matches(cls, sequence: str) -> bool:
        return sequence in cls._aliases

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str:
        return cls._aliases[sequence]

    @staticmethod
    def _get_type_for_sequence(sequence: str) -> type[Event]:
        for klass in Event._subclasses:
            if klass._matches(sequence):
                return klass

        raise InvalidBindingSequenceError(sequence)


class KeyboardEvent(Event):
    _ignored_values = (None, "", "??", -1, 0, (), set())
    _relevant_attrs = ("char", "modifiers", "keysymbol", "keycode")

    _aliases = {
        "<KeyDown:Any>": "<KeyPress>",
        "<KeyDown>": "<KeyPress>",
        "<KeyUp:Any>": "<KeyRelease>",
        "<KeyUp>": "<KeyRelease>",
    }

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[tuple(self._subst.keys()).index(item)]
            if value == "??":
                setattr(self, item, None)
                return

            value = Tcl.from_(self._subst[item][1], value)
            if item == "keysymbol" and value in KEYSYM_ALIASES:
                value = KEYSYM_ALIASES[value]
            elif item == "modifiers":
                value = get_modifiers(value)

            setattr(self, item, value)

    @classmethod
    def _matches(cls, sequence: str) -> bool:
        return sequence in cls._aliases or bool(re.match(KEYBOARD_EVENT_REGEX, sequence))

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str | None:
        if sequence in cls._aliases:
            return cls._aliases[sequence]

        search = re.search(KEYBOARD_EVENT_REGEX, sequence)
        assert search is not None

        press_release = {"Down": "Press", "Up": "Release"}[search[1]]

        keys = search[2].split("-")
        key = REV_KEYSYM_ALIASES.get(keys[-1], keys[-1])
        if key == "Any":
            key = ""

        modifiers = keys[:-1]
        tcl_modifiers = []
        for mod in modifiers:
            mod = BINDING_MODIFIER_MAP.get(mod)
            if not mod:
                return None
            tcl_modifiers.append(mod)

        if "Shift" in tcl_modifiers:
            if len(key) == 1:
                key = key.upper()
            elif key == "Tab" and Tcl.windowing_system == "x11":
                tcl_modifiers.remove("Shift")
                key = "ISO_Left_Tab"

        return f"<{'-'.join(tcl_modifiers)}{'-' if tcl_modifiers else ''}Key{press_release}{f'-{key}' if key else ''}>"


class MouseEvent(Event):
    _relevant_attrs = ("button", "modifiers", "abs_x", "abs_y", "rel_x", "rel_y")
    _aliases = {
        # button press
        "MouseDown": "ButtonPress",
        "MouseDown:Any": "ButtonPress",
        "MouseDown:Any:Double": "Double-ButtonPress",
        "MouseDown:Any:Triple": "Triple-ButtonPress",
        "MouseDown:Any:Triple": "Quadruple-ButtonPress",
        "MouseDown:Left": "ButtonPress-{left}",
        "MouseDown:Left:Double": "Double-ButtonPress-{left}",
        "MouseDown:Left:Triple": "Triple-ButtonPress-{left}",
        "MouseDown:Left:Quadruple": "Quadruple-ButtonPress-{left}",
        "MouseDown:Middle": "ButtonPress-{middle}",
        "MouseDown:Middle:Double": "Double-ButtonPress-{middle}",
        "MouseDown:Middle:Triple": "Triple-ButtonPress-{middle}",
        "MouseDown:Middle:Quadruple": "Quadruple-ButtonPress-{middle}",
        "MouseDown:Right": "ButtonPress-{right}",
        "MouseDown:Right:Double": "Double-ButtonPress-{right}",
        "MouseDown:Right:Triple": "Triple-ButtonPress-{right}",
        "MouseDown:Right:Quadruple": "Quadruple-ButtonPress-{right}",
        # drag
        "MouseDrag:Left": "Button{left}-Motion",
        "MouseDrag:Middle": "Button{middle}-Motion",
        "MouseDrag:Right": "Button{right}-Motion",
        # button release
        "MouseUp:Any": "ButtonRelease",
        "MouseUp:Left": "ButtonRelease-{left}",
        "MouseUp:Middle": "ButtonRelease-{middle}",
        "MouseUp:Right": "ButtonRelease-{right}",
        "MouseUp": "ButtonRelease",
        # mouse motion
        "MouseEnter": "Enter",
        "MouseLeave": "Leave",
        "MouseMove": "Motion",
    }

    def __init__(self, *args) -> None:
        for item in self._relevant_attrs:
            value = args[tuple(self._subst.keys()).index(item)]
            if value == "??":
                setattr(self, item, None)
                continue

            value: T = Tcl.from_(self._subst[item][1], value)
            if item == "button":
                if value in (4, 5):
                    # FIXME: this sholdn't be this way
                    self.button = None
                    continue
                value = Mouse(reversed_dict(BUTTON_NUMS)[value])
            elif item == "modifiers":
                value = get_modifiers(value)

            setattr(self, item, value)

    @classmethod
    def _matches(cls, sequence: str) -> bool:
        modifiers = re.findall(KEYBOARD_MODIFIERS_REGEX, sequence)
        match = re.match("<(.*?)-(.*?)>", sequence)
        if match is None:
            mouse_sequence = sequence.strip("<>")
        elif set(match[1].split("-")) != set(modifiers):
            return False
        else:
            mouse_sequence = match[2]
        return mouse_sequence in cls._aliases

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str | None:
        modifiers = re.findall(KEYBOARD_MODIFIERS_REGEX, sequence)
        match = re.match("<(.*)-(.*)>", sequence)

        tcl_modifiers = []
        for mod in modifiers:
            mod = BINDING_MODIFIER_MAP.get(mod)
            if not mod:
                return None
            tcl_modifiers.append(mod)

        mouse_sequence = match[2] if match is not None else sequence.strip("<>")
        return f"<{'-'.join(tcl_modifiers)}{'-' if tcl_modifiers else ''}{cls._aliases[mouse_sequence].format(**BUTTON_NUMS)}>"


class ScrollEvent(MouseEvent):
    _ignored_values = (None, "??", set())
    _relevant_attrs = ("delta", "modifiers")
    _aliases = {
        "MouseWheel": "MouseWheel",
        "Wheel:Up": "Button-4",
        "Wheel:Down": "Button-5",
    }

    def __init__(self, *args) -> None:
        order = tuple(self._subst.keys())

        if Tcl.windowing_system == "x11":
            self.delta = -1 if Tcl.from_(int, args[order.index("button")]) == 4 else 1
        else:
            self.delta = Tcl.from_(int, args[order.index("delta")])

        self.modifiers = get_modifiers(Tcl.from_(int, args[order.index("modifiers")]))


class StateEvent(Event):
    ...


class WindowManagerEvent(Event):
    _relevant_attrs: tuple[str, ...] = ("window",)
    _subst = {"widget": (r"%W", str)}
    _aliases = {
        "<Maximize>": "<<Maximize>>",
        "<Minimize>": "<<Minimize>>",
        "<Hide>": "<<Hide>>",
        "<Unhide>": "<<Unhide>>",
        "<Restore>": "<<Restore>>",
        "<EnterFullscreen>": "<<Fullscreen>>",
        "<ExitFullscreen>": "<<Unfullscreen>>",
        "<ContextHelp>": "<<__context_help_private__>>",
    }

    def __init__(self, *args) -> None:
        from tukaan._base import ToplevelBase

        assert len(args) == 1
        self.window = Tcl.call(ToplevelBase, "winfo", "toplevel", args[0])


class VirtualEvent(Event):
    _subst = {"data": ("%d", int)}

    def __init__(self, *args) -> None:
        self.data = _virtual_event_data_container.pop(Tcl.from_(str, args[0]))

    def __repr__(self) -> str:
        plus_str = "" if self.data is None else f": data={self.data!r}"
        return f"<VirtualEvent: {self.sequence}{plus_str}>"

    @classmethod
    def _matches(cls, sequence: str) -> bool:
        return sequence.startswith("<<") and sequence.endswith(">>") and len(sequence) > 4

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str:
        return sequence
