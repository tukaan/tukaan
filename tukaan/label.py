from typing import Any, Dict, Tuple, Union, Literal

from ._base import BaseWidget, TkWidget


class Label(BaseWidget):
    _keys: Dict[str, Union[Any, Tuple[Any, str]]] = {
        "anchor": str,
        "focusable": (bool, "takefocus"),
        "justify": str,
        "max_line_length": (int, "wraplength"),
        "style": str,
        "text": str,
    }

    _anchors: Dict[Union[str, None], Union[str, None]] = {
        None: None,
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

    def __init__(
        self,
        parent: Union[TkWidget, None] = None,
        anchor: Union[
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
            ],
            None,
        ] = None,
        focusable: Union[bool, None] = None,
        justify: Union[Literal["left", "center", "right"], None] = None,
        max_line_length: Union[int, None] = None,
        style: Union[str, None] = None,
        text: Union[str, None] = None,
    ) -> None:

        anchor = self._anchors[anchor]

        BaseWidget.__init__(
            self,
            parent,
            "ttk::label",
            anchor=anchor,
            takefocus=focusable,
            justify=justify,
            wraplength=max_line_length,
            style=style,
            text=text,
        )
