from __future__ import annotations

import re
from functools import partial
from pathlib import Path
from typing import Any, Callable

from PIL import Image, UnidentifiedImageError  # type: ignore

from ._info import System
from ._keysyms import _keysym_aliases
from ._tcl import Tcl
from ._utils import reversed_dict
from .colors import Color

if System.os == "macOS":
    button_numbers = {1: "left", 2: "right", 3: "middle", None: None}
    modifier_order = {"Alt_Opt": "⌥", "Shift": "⇧", "Ctrl_Ctrl": "⌃", "Ctrl_Cmd": "⌘"}
    platform_sortcuts = {"Preferences": ("Ctrl_Cmd", ","), "Help": ("Ctrl_Cmd", "?")}
    shortcut_separator = ""
else:
    button_numbers = {1: "left", 2: "middle", 3: "right", None: None}
    modifier_order = {"Ctrl_Ctrl": "Ctrl", "Ctrl_Cmd": "Ctrl", "Alt_Opt": "Alt", "Shift": "Shift"}
    platform_sortcuts = {"Preferences": ("Ctrl_Cmd", "."), "Help": ("F1",)}  # type: ignore  # mypy doesn't like ("F1",)
    shortcut_separator = "+"


class DataContainer:
    _container_dict: dict[str, Any] = {}

    def add(self, value: Any) -> str:
        key = str(id(value))
        self._container_dict[key] = value
        return key

    def pop(self, key: str) -> Any:
        return self._container_dict.pop(key, None)

    def __getitem__(self, key: str) -> Any:
        return self._container_dict[key]


_virtual_event_data_container = DataContainer()


class Event:
    binding_substitutions: dict[str, tuple[str, type | tuple[type]]] = {
        "button": ("%b", int),
        "modifiers": ("%s", int),
        "keycode": ("%k", int),
        "rel_x": (r"%x", int),
        "rel_y": (r"%y", int),
        "char": ("%A", str),
        "delta": ("%D", float),
        "keysymbol": ("%K", str),
        "abs_x": (r"%X", int),
        "abs_y": (r"%Y", int),
    }
    _modifiers = {
        0x1000: "MouseWheel:Down",
        0x800: "MouseWheel:Up",
        0x400: "MouseButton:Right",
        0x200: "MouseButton:Middle",
        0x100: "MouseButton:Left",
        0x80: "AltGr",
        0x40: "Super",
        0x20: "idk",  # TODO
        0x10: "NumLock",
        0x8: "Alt",
        0x4: "Control",
        0x2: "CapsLock",
        0x1: "Shift",
    }

    sequence: str
    sequences: dict[str, str]

    _ignored_values: tuple[Any, ...] = (None, "??", -1, 0)
    _order: tuple[str, ...] = tuple(binding_substitutions.keys())
    _relevant_attributes: tuple[str, ...] = ()
    _result = True

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return cls.sequences[sequence]

    def __init__(self, *args) -> None:
        for item in self._relevant_attributes:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self.binding_substitutions[item][1], value)
            else:
                value = None
            setattr(self, item, value)

    def __repr__(self) -> str:
        pairs = []

        for name in self._relevant_attributes:
            value = getattr(self, name)
            if value not in self._ignored_values:
                pairs.append(f"{name}={value!r}")

        return f"<{type(self).__name__}: {', '.join(pairs)}>"

    def _get_modifiers(self, value: int) -> set[str]:
        result = []

        for modifier_value in self._modifiers:
            # tkinter uses some crazy bit shifting stuff here that makes me dizzy
            # imo my solution is much more clear
            if value >= modifier_value:
                value -= modifier_value
                result.append(self._modifiers[modifier_value])

        return set(result)

    def stop(self):
        self._result = False
        return self._result


class KeyboardEvent(Event):
    sequences = {
        "<KeyDown:Any>": "<KeyPress>",
        "<KeyDown>": "<KeyPress>",
        "<KeyUp:Any>": "<KeyRelease>",
        "<KeyUp>": "<KeyRelease>",
    }

    _ignored_values: tuple[Any, ...] = (None, "", "??", -1, 0, (), set())
    _regex_str = r"<Key(Down|Up):\((.*?)\)>"
    _relevant_attributes = ("char", "modifiers", "keysymbol", "keycode")
    _reversed_aliases = reversed_dict(_keysym_aliases)

    @classmethod
    def _matches(cls, sequence: str) -> bool:
        return sequence in cls.sequences or bool(re.match(cls._regex_str, sequence))

    @classmethod
    def _parse(cls, sequence: str) -> str:
        up_or_down = {"Down": "Press", "Up": "Release"}

        if sequence in cls.sequences:
            return cls.sequences[sequence]
        elif re.match(cls._regex_str, sequence):
            search = re.search(cls._regex_str, sequence)
            assert search is not None  # mypy

            keys = search[2].split("-")
            key = keys[-1]
            if key in cls._reversed_aliases:
                key = cls._reversed_aliases[key]

            modifier_keys = keys[:-1]
            for mod in modifier_keys:
                if mod in cls._reversed_aliases:
                    modifier_keys.remove(mod)
                    modifier_keys.append(cls._reversed_aliases[mod])

            if "Shift" in modifier_keys:
                if len(key) == 1:
                    key = key.upper()
                elif key == "Tab" and System.win_sys == "X11":
                    modifier_keys.remove("Shift")
                    key = "ISO_Left_Tab"

            modifiers = "-".join(modifier_keys) + ("-" if modifier_keys else "")

            return f"<{modifiers}Key{up_or_down[search[1]]}-{key}>"

        raise ValueError

    def __init__(self, *args) -> None:
        for item in self._relevant_attributes:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self.binding_substitutions[item][1], value)
            else:
                value = None

            if item == "keysymbol" and value in _keysym_aliases:
                value = _keysym_aliases[value]

            if item == "modifiers":
                value = self._get_modifiers(value)

            setattr(self, item, value)


class MouseEvent(Event):
    sequences = {
        # button press
        "<MouseDown:Any:Double>": "<Double-ButtonPress>",
        "<MouseDown:Any:Triple>": "<Triple-ButtonPress>",
        "<MouseDown:Any>": "<ButtonPress>",
        "<MouseDown:Left:Double>": "<Double-ButtonPress-1>",
        "<MouseDown:Left:Triple>": "<Triple-ButtonPress-1>",
        "<MouseDown:Left>": "<ButtonPress-1>",
        "<MouseDown:Middle:Double>": "<Double-ButtonPress-2>",
        "<MouseDown:Middle:Triple>": "<Triple-ButtonPress-2>",
        "<MouseDown:Middle>": "<ButtonPress-2>",
        "<MouseDown:Right:Double>": "<Double-ButtonPress-3>",
        "<MouseDown:Right:Triple>": "<Triple-ButtonPress-3>",
        "<MouseDown:Right>": "<ButtonPress-3>",
        "<MouseDown>": "<ButtonPress>",
        # drag
        "<MouseDrag:Left>": "<Button1-Motion>",
        "<MouseDrag:Middle>": "<Button2-Motion>",
        "<MouseDrag:Right>": "<Button3-Motion>",
        # button release
        "<MouseUp:Any>": "<ButtonRelease>",
        "<MouseUp:Left>": "<ButtonRelease-1>",
        "<MouseUp:Middle>": "<ButtonRelease-2>",
        "<MouseUp:Right>": "<ButtonRelease-3>",
        "<MouseUp>": "<ButtonRelease>",
        # mouse motion
        "<MouseEnter>": "<Enter>",
        "<MouseLeave>": "<Leave>",
        "<MouseMotion>": "<Motion>",
        # focus (i have no better idea where to put them)
        "<FocusOut>": "<FocusOut>",
        "<FocusIn>": "<FocusIn>",
    }
    _ignored_values: tuple[Any, ...] = (None, "??", -1, 0, set())
    _relevant_attributes = ("button", "modifiers", "abs_x", "abs_y", "rel_x", "rel_y")

    def __init__(self, *args) -> None:
        for item in self._relevant_attributes:
            value = args[self._order.index(item)]
            if value != "??":
                value = Tcl.from_(self.binding_substitutions[item][1], value)
            else:
                value = None

            if value and item == "button":
                value = button_numbers[value]

            if item == "modifiers":
                value = self._get_modifiers(value)

            setattr(self, item, value)


class ScrollEvent(Event):
    _ignored_values: tuple[Any, ...] = (None, "??", set())
    _relevant_attributes = ("delta", "modifiers")

    @classmethod
    def _matches(cls, sequence) -> bool:
        return any(i in sequence for i in ("MouseWheel", "Button-4", "Button-5"))

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return sequence

    def __init__(self, *args) -> None:
        if System.win_sys == "X11":
            num = Tcl.from_(int, args[self._order.index("button")])
            self.delta = -1 if num == 4 else 1
        else:
            self.delta = Tcl.from_(int, args[self._order.index("delta")])

        self.modifiers = self._get_modifiers(Tcl.from_(int, args[self._order.index("modifiers")]))


class VirtualEvent(Event):
    binding_substitutions = {"data": ("%d", int)}

    @classmethod
    def _matches(cls, sequence) -> bool:
        return sequence.startswith("<<") and sequence.endswith(">>") and len(sequence) > 4

    @classmethod
    def _parse(cls, sequence: str) -> str:
        return sequence

    def __init__(self, *args) -> None:
        data_key = Tcl.from_(str, args[0])

        self.data = _virtual_event_data_container.pop(data_key) if data_key else None

    def __repr__(self) -> str:
        return f"<VirtualEvent: {self.sequence.strip('<').strip('>')}; data={self.data!r}>"


class DnDEvent(Event):
    binding_substitutions = {
        "action": ("%A", str),
        "button": ("%b", int),
        "common_formats": ("%CST", (str,)),
        "_data": ("%D", str),
        "format": ("%T", str),
        "formats": ("%L", (str,)),
        "type": ("%CPT", str),
        "rel_x": (r"%X", int),
        "rel_y": (r"%Y", int),
    }
    sequences = {
        # drop
        "<<Drop:Any>>": "<<Drop:*>>",
        "<<Drop:App>>": "<<Drop:DND_App>>",
        "<<Drop:Color>>": "<<Drop:DND_Color>>",
        "<<Drop:Custom>>": "<<Drop:DND_UserDefined>>",
        "<<Drop:File>>": "<<Drop:DND_Files>>",
        "<<Drop:HTML>>": "<<Drop:DND_HTML>>",
        "<<Drop:RTF>>": "<<Drop:DND_RTF>>",
        "<<Drop:Text>>": "<<Drop:DND_Text>>",
        "<<Drop:URL>>": "<<Drop:DND_URL>>",
        "<<Drop>>": "<<Drop>>",
        # drag
        "<<DragEnd>>": "<<DragEndCmd>>",
        "<<DragEnter>>": "<<DropEnter>>",
        "<<DragLeave>>": "<<DropLeave>>",
        "<<DragMotion>>": "<<DropPosition>>",
        "<<DragStart>>": "<<DragInitCmd>>",
    }

    _existing_types = {
        # cross-platform
        "DND_App",
        "DND_Color",
        "DND_Files",
        "DND_HTML",
        "DND_RTF",
        "DND_Text",
        "DND_URL",
        # tkdnd_macosx.tcl
        "NSPasteboardTypeString",
        "NSFilenamesPboardType",
        "NSPasteboardTypeHTML",
        # tkdnd_windows.tcl
        "CF_UNICODETEXT",
        "CF_TEXT",
        "CF_HDROP",
        "UniformResourceLocator",
        "CF_HTML",
        "HTML Format",
        "CF_RTF",
        "CF_RTFTEXT",
        "Rich Text Format",
        # tkdnd_unix.tcl
        r"text/plain\;charset=utf-8",
        "UTF8_STRING",
        "text/plain",
        "text/rtf",
        "text/richtext",
        "STRING",
        "TEXT",
        "COMPOUND_TEXT",
        "text/uri-list",
        r"text/html\;charset=utf-8",
        "text/html",
        "application/x-color",
        # add more of these app-specific types?
        # tkdnd raises an error, if there's no common types between source and dest
        "application/x-orgkdeplasmataskmanager_taskbuttonitem",
        "text/x-orgkdeplasmataskmanager_taskurl",
    }
    _dnd_type_aliases = {
        "app": "DND_App",
        "color": "DND_Color",
        "custom": "DND_UserDefined",
        "file": "DND_Files",
        "html": "DND_HTML",
        "rtf": "DND_RTF",
        "text": "DND_Text",
        "url": "DND_URL",
    }
    _result = "copy"

    type: str
    format: str
    action: str

    def __init__(self, *args) -> None:
        result = {}

        for (attr, (_, type_)), value in zip(self.binding_substitutions.items(), args):
            value = Tcl.from_(type_, value) if value != "??" else None
            result[attr] = value

        try:
            dropped_data_type = result["type"] = reversed_dict(self._dnd_type_aliases)[
                result["type"]
            ]
        except KeyError:
            dropped_data_type = None

        self._needs_download = False
        self._image_regex = re.compile(r'(.*?)<img (.*?)src="(.*?)"(.*?)>(.*?)', re.DOTALL)

        if dropped_data_type == "file":
            data = Tcl.from_([str], result["_data"])

            result["_data"] = [Path(x) for x in data] if len(data) > 1 else Path(data[0])
        elif dropped_data_type == "html":
            # search for an image url in the dropped html, and return a PIL.Image.Image object
            if re.match(self._image_regex, result["_data"]):
                result["_data"]
                self._needs_download = True

        elif dropped_data_type == "color":
            color = "#"
            splitted_color = Tcl.from_([str], result["_data"])

            if len(splitted_color) == 4:
                for i in splitted_color[:3]:
                    color += i[4:]
            else:
                color = result["_data"]

            result["_data"] = Color(color)

        elif dropped_data_type == "custom":
            ord_list = Tcl.from_([str], result["_data"])
            char_tuple = tuple(
                chr(int(x)) for x in ord_list
            )  # faster to int() here than in Tcl.from_

            result["_data"] = "".join(char_tuple)

        result["button"] = button_numbers[result["button"]]

        for key, value in result.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        if self.type == "custom":
            more_useful_type_info = f", format={self.format!r}"
        else:
            more_useful_type_info = f", type={self.type!r}"

        if "Drop" in self.sequence:
            data_or_xy = f"data={self.data!r}"
        else:
            data_or_xy = f"rel_x={self.rel_x}, rel_y={self.rel_y}"

        return f"<DnDEvent: {data_or_xy}, action={self.action!r}{more_useful_type_info}>"

    @property
    def data(self) -> str | list | Image.Image | Path | Color:
        if self._needs_download:
            import tempfile

            import requests

            try:
                path = re.search(self._image_regex, self._data)[3]  # type: ignore
                _, name = tempfile.mkstemp()

                with open(name, "wb") as file:
                    file.write(requests.get(path).content)

                self._data = Image.open(name)
            except requests.exceptions.ConnectionError:
                pass
            except UnidentifiedImageError:
                self._needs_download = False
            else:
                self._needs_download = False

        return self._data

    def ignore(self):
        self._result = "refuse_drop"
        return self._result

    def move(self):
        self._result = "move"
        return self._result

    def copy(self):
        self._result = "copy"
        return self._result

    def link(self):
        self._result = "link"
        return self._result

    def stop(self):
        self._result = "refuse_drop"
        return self._result


class EventMixin:
    _name: str

    def _bind(self, sequence: str, func: Callable | str, overwrite: bool, send_event: bool) -> None:
        event: type[KeyboardEvent | MouseEvent | ScrollEvent | DnDEvent | VirtualEvent]

        if KeyboardEvent._matches(sequence):
            event = KeyboardEvent
        elif sequence in MouseEvent.sequences:
            event = MouseEvent
        elif ScrollEvent._matches(sequence):
            event = ScrollEvent
        elif sequence in DnDEvent.sequences:
            event = DnDEvent
        elif VirtualEvent._matches(sequence):
            event = VirtualEvent
        else:
            raise ValueError(f"invalid event sequence: {sequence}")
        _orig_seq = sequence

        def real_func(func, *args):
            if not send_event:
                return func()

            event_to_send = event(*args)
            event_to_send.sequence = _orig_seq
            result = func(event_to_send)

            if result is not None:
                return result

            return event_to_send._result

        script_str = func  # for internal bindings, where i use strings for tcl scripts, or when unbinding where func is ""

        if callable(func):
            cmd = Tcl.create_cmd(partial(real_func, func))

            sequence = event._parse(sequence)

            subst_str = " ".join(item[0] for item in event.binding_substitutions.values())

            if event is DnDEvent:
                script_str = (
                    f"{'' if overwrite else '+'} {cmd} {subst_str}"  # tcl: {+ command %subst}
                )
            else:
                script_str = f"{'' if overwrite else '+'} if {{[{cmd} {subst_str}] == 0}} break"  # tcl: {+ if {[command %subst] == 0} break}

        Tcl.call(None, "bind", self._name if self._name != ".app" else ".", sequence, script_str)

    def bind(
        self,
        sequence: str,
        func: str | Callable[[], bool | None] | Callable[[Event], bool | None],
        *,
        overwrite: bool = False,
        send_event: bool = False,
    ) -> None:
        if isinstance(sequence, KeySeq):
            sequence = sequence.event_sequence

        if "MouseScroll" in sequence:
            if System.win_sys == "X11":
                self._bind(sequence.replace("MouseScroll", "Button-4"), func, overwrite, send_event)
                self._bind(sequence.replace("MouseScroll", "Button-5"), func, overwrite, send_event)
                return
            else:
                sequence = sequence.replace("MouseScroll", "MouseWheel")

        if "Menu" in sequence and System.os == "Windows":
            sequence = sequence.replace("Menu", "App")

        self._bind(sequence, func, overwrite, send_event)

    def unbind(self, sequence: str) -> None:
        self._bind(sequence, "", True, False)

    def generate_event(self, sequence: str, data: Any = None) -> None:
        global _virtual_event_data_container
        key = _virtual_event_data_container.add(data) if data is not None else None

        Tcl.call(None, "event", "generate", self, sequence, *Tcl.to_tcl_args(data=key))


def DragObject(
    data: str | list | tuple | Path | Color, type_: str | None = None, action: str = "copy"
) -> tuple[str, str, str]:
    if type_ is None:
        if isinstance(data, str):
            type_ = "DND_Text"
        elif isinstance(data, (Path, tuple, list)):  # List or tuple of Paths
            type_ = "DND_Files"
        elif isinstance(data, Color):
            type_ = "DND_Color"
        else:
            raise ValueError("can't detect DnD type automatically. Please specify it!")
    else:
        try:
            type_ = DnDEvent._dnd_type_aliases[type_]
        except KeyError:
            if type_ not in DnDEvent._existing_types:
                Tcl.eval(
                    None,
                    f"lappend tkdnd::generic::_platform2tkdnd {type_} DND_UserDefined"
                    + "\n"
                    + f"lappend tkdnd::generic::_tkdnd2platform [dict get $tkdnd::generic::_platform2tkdnd {type_}] {type_}",
                )

    return (action, type_, Tcl.to(data))


class KeySeq:
    _wrong_modifiers = {
        "Alt": "'Alt_Opt'",
        "Command": "'Ctrl_Cmd'",
        "Control": "'Ctrl_Cmd' or 'Ctrl_Ctrl'",
    }
    _preset_shortcuts = {
        "bold": ("Ctrl_Cmd", "b"),
        "close": ("Ctrl_Cmd", "w"),
        "copy": ("Ctrl_Cmd", "c"),
        "cut": ("Ctrl_Cmd", "x"),
        "find": ("Ctrl_Cmd", "f"),
        "italic": ("Ctrl_Cmd", "i"),
        "new": ("Ctrl_Cmd", "n"),
        "open": ("Ctrl_Cmd", "o"),
        "paste": ("Ctrl_Cmd", "v"),
        "print": ("Ctrl_Cmd", "p"),
        "quit": ("Ctrl_Cmd", "q"),
        "redo": ("Ctrl_Cmd", "y"),
        "refresh": ("F5",),
        "save as": ("Ctrl_Cmd", "Shift", "s"),
        "save": ("Ctrl_Cmd", "s"),
        "underline": ("Ctrl_Cmd", "u"),
        "undo": ("Ctrl_Cmd", "z"),
        "zoom in": ("Ctrl_Cmd", "+"),
        "zoom out": ("Ctrl_Cmd", "-"),
    }
    _preset_shortcuts.update(platform_sortcuts)

    def __init__(self, *args) -> None:
        if args[0] in self._preset_shortcuts:
            self._sequence = list(self._preset_shortcuts[args[0]])
        else:
            seq = []
            real_key = ""

            for key in list(args):
                if key in self._wrong_modifiers:
                    raise ValueError(
                        f"wrong modifier key: {key!r}. Use {self._wrong_modifiers[key]} instead."
                    )
                elif " " in key:
                    raise ValueError(f"invalid key: {key!r}")

                if key in modifier_order:
                    seq.append(key)
                else:
                    real_key = key

            seq.append(real_key)
            self._sequence = seq

    @property
    def event_sequence(self) -> str:
        return f"<KeyDown:({'-'.join(self._sequence)})>"

    @property
    def shortcut_sequence(self) -> str:
        real_key = self._sequence[-1]

        result = [symbol for name, symbol in modifier_order.items() if name in self._sequence]

        result.append(real_key.upper())

        return shortcut_separator.join(result)

    def __eq__(self, other: object) -> bool:
        return (
            set(self._sequence) == set(other._sequence)
            if isinstance(other, KeySeq)
            else NotImplemented
        )
