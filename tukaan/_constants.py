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
