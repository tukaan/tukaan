from __future__ import annotations

from typing import Any, Literal, Optional

AnchorAnnotation = Optional[
    Literal[
        "bottom",
        "bottom-left",
        "bottom-right",
        "center",
        "left",
        "right",
        "top",
        "top-left",
        "top-right",
    ]
]

_anchors: dict[Any, str] = {
    None: "",
    "bottom": "s",
    "bottom-left": "sw",
    "bottom-right": "se",
    "center": "center",
    "left": "w",
    "right": "e",
    "top": "n",
    "top-left": "nw",
    "top-right": "ne",
}

_wraps = {"word": "word", "letter": "char", None: "none"}

_cursor_styles = {"block": True, "normal": False}

_inactive_cursor_styles = {"hollow": "hollow", "solid": "solid", None: "none"}

_window_pos: set[str] = {"center", "top-left", "top-right", "bottom-left", "bottom-right"}

_resizable = {
    False: (0, 0),
    "horizontal-only": (1, 0),
    "vertical-only": (0, 1),
    True: (1, 1),
}

_VALID_STATES: set[str] = {
    "active",
    "alternate",
    "background",
    "disabled",
    "focus",
    "hover",
    "invalid",
    "pressed",
    "readonly",
    "selected",
}

_BINDING_ALIASES = {
    "<KeyDown>": "<KeyPress>",
    "<KeyUp>": "<KeyRelease>",
    "<MouseDown:Left>": "<ButtonPress-1>",
    "<MouseDown:Middle>": "<ButtonPress-2>",
    "<MouseDown:Right>": "<ButtonPress-3>",
    "<MouseDown>": "<ButtonPress>",
    "<MouseEnter>": "<Enter>",
    "<MouseLeave>": "<Leave>",
    "<MouseMove>": "<Motion>",
    "<MouseUp:Left>": "<ButtonRelease-1>",
    "<MouseUp:Middle>": "<ButtonRelease-2>",
    "<MouseUp:Right>": "<ButtonRelease-3>",
    "<MouseUp>": "<ButtonRelease>",
    "<MouseWheelRotate>": "<MouseWheel>",
}

_KEYSYMS = {
    "Space": "space",
    "!": "exclam",
    "#": "numbersign",
    "$": "dollar",
    "%": "percent",
    "&": "ampersand",
    "'": "apostrophe",
    "(": "parenleft",
    ")": "parenright",
    "*": "asterisk",
    "+": "plus",
    ",": "comma",
    "-": "minus",
    ".": "period",
    "/": "slash",
    ":": "colon",
    ";": "semicolon",
    "<": "less",
    "=": "equal",
    ">": "greater",
    "?": "question",
    "@": "at",
    "[": "bracketleft",
    "\\": "backslash",
    "]": "bracketright",
    "^": "asciicircum",
    "_": "underscore",
    "`": "grave",
    "{": "braceleft",
    "|": "bar",
    "}": "braceright",
    "~": "asciitilde",
    "¡": "exclamdown",
    "¤": "currency",
    "§": "section",
    "¨": "diaeresis",
    "°": "degree",
    "±": "plusminus",
    "´": "acute",
    "¶": "paragraph",
    "¸": "cedilla",
    "¿": "questiondown",
    "Á": "Aacute",
    "Ä": "Adiaeresis",
    "Å": "Aring",
    "É": "Eacute",
    "Í": "Iacute",
    "×": "multiply",
    "ß": "ssharp",
    "á": "aacute",
    "ä": "adiaeresis",
    "å": "aring",
    "é": "eacute",
    "í": "iacute",
    "÷": "division",
    "Đ": "Dstroke",
    "đ": "dstroke",
    "Ł": "Lstroke",
    "ł": "lstroke",
    "˘": "breve",
    "˛": "ogonek",
    "˝": "doubleacute",
    '"': "quotedbl",
    "Backspace": "BackSpace",
    "Enter": "Return",
}
