from __future__ import annotations

import re

from tukaan._misc import Mouse
from tukaan._tcl import Tcl
from tukaan._typing import T
from tukaan._utils import reversed_dict

from .constants import BINDING_MODIFIER_MAP, BUTTON_NUMS, KEYBOARD_MODIFIERS_REGEX, MODIFIER_MAP


def get_modifiers(value: int) -> set[str]:
    result = []

    for modifier_value in MODIFIER_MAP:
        if value >= modifier_value:
            value -= modifier_value
            result.append(MODIFIER_MAP[modifier_value])

    return set(result)


class InvalidBindingSequenceError(Exception):
    def __init__(self, sequence: str) -> None:
        super().__init__(f"not a valid binding sequence: {sequence}")


class Event:
    _ignored_values: tuple[object, ...] = (None, "??", set())
    _relevant_attrs: tuple[str, ...]
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

    @staticmethod
    def _get_type_for_sequence(sequence: str) -> type[Event]:
        return MouseEvent

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str:
        return sequence


class KeyboardEvent(Event):
    ...


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
                value = None
            else:
                value: T = Tcl.from_(self._subst[item][1], value)

            if value and item == "button":
                value = Mouse(reversed_dict(BUTTON_NUMS).get(value))
            elif item == "modifiers":
                value = get_modifiers(value)

            setattr(self, item, value)

    @classmethod
    def _get_tcl_sequence(cls, sequence: str) -> str | None:
        modifiers = re.findall(KEYBOARD_MODIFIERS_REGEX, sequence)
        match = re.match("<(.*)-(.*)>", sequence)
        if match is not None and set(match[1].split("-")) != set(modifiers):
            raise InvalidBindingSequenceError(sequence)

        tcl_modifiers = []
        for modifier in modifiers:
            modifier = BINDING_MODIFIER_MAP.get(modifier)
            if not modifier:
                return None
            tcl_modifiers.append(modifier)

        mouse_sequence = match[2] if match is not None else sequence.strip("<>")
        return f"<{'-'.join(tcl_modifiers)}{'-' if tcl_modifiers else ''}{cls._aliases[mouse_sequence].format(**BUTTON_NUMS)}>"


class ScrollEvent(Event):
    ...


class VirtualEvent(Event):
    ...


class StateEvent(Event):
    ...


class WindowManagerEvent(Event):
    ...
