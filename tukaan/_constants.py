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

_window_pos: set[str] = {
    "center",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
}
