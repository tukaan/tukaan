from typing import Any, Dict, Literal, Optional, Set

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

_anchors: Dict[Any, str] = {
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

_window_pos: Set[str] = {
    "center",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
}
