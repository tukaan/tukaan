from typing import Literal, Optional, Tuple, Union, Dict
from ._misc import ScreenDistance
from ._utils import py_to_tcl_arguments


class LayoutManager:
    def __init__(self, widget):
        self._widget = widget

    def _parse_margin(self, to_parse):
        if to_parse is None:
            return None, None

        if isinstance(to_parse, int):
            return ((to_parse,) * 2,) * 2

        elif len(to_parse) == 2:
            return ((to_parse[1], to_parse[1]), (to_parse[0],) * 2)

        elif len(to_parse) == 3:
            return ((to_parse[1],) * 2, (to_parse[0], to_parse[2]))

        elif len(to_parse) == 4:
            return ((to_parse[3], to_parse[1]), (to_parse[0], to_parse[2]))

    def _parse_sticky_values(self, hor, vert):
        # maybe there are a simpler solution, than write out all the
        # possibilities, but i'd like have a table of them
        return {
            ("left", "bottom"): "sw",
            ("left", "stretch"): "nsw",
            ("left", "top"): "nw",
            ("left", None): "w",
            ("right", "bottom"): "se",
            ("right", "stretch"): "nse",
            ("right", "top"): "ne",
            ("right", None): "e",
            ("stretch", "bottom"): "sew",
            ("stretch", "stretch"): "nsew",
            ("stretch", "top"): "new",
            ("stretch", None): "ew",
            (None, "bottom"): "s",
            (None, "stretch"): "ns",
            (None, "top"): "n",
            (None, None): "",
        }[(hor, vert)]

    def _parse_possibly_relative_values(
        self,
        result_dict: Dict,
        values: Tuple[Union[int, str, ScreenDistance]],
        names: Tuple[str],
    ):
        for name, value in zip(names, values):
            if value is None:
                continue
            elif isinstance(value, str) and value.endswith("%"):
                result_dict[f"rel{name}"] = float(value[:-1]) / 100
            else:
                result_dict[name] = value

    def grid(
        self,
        col: Optional[int] = None,
        colspan: Optional[int] = None,
        hor_align: Optional[Literal["right", "left", "stretch"]] = None,
        margin: Optional[Union[int, Tuple[int]]] = None,
        row: Optional[int] = None,
        rowspan: Optional[int] = None,
        vert_align: Optional[Literal["top", "bottom", "stretch"]] = None,
    ):
        padx, pady = self._parse_margin(margin)
        print(padx, pady)

        self._widget._tcl_call(
            None,
            "grid",
            self._widget,
            *py_to_tcl_arguments(
                column=col,
                columnspan=colspan,
                padx=padx,
                pady=pady,
                row=row,
                rowspan=rowspan,
                sticky=self._parse_sticky_values(hor_align, vert_align),
            ),
        )

    def position(
        self,
        x: Optional[Union[int, str]] = None,
        y: Optional[Union[int, str]] = None,
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
    ):
        possibly_relative_values_dict = {}
        self._parse_possibly_relative_values(
            possibly_relative_values_dict,
            (x, y, width, height),
            ("x", "y", "width", "height"),
        )

        print(possibly_relative_values_dict)

        self._widget._tcl_call(
            None, "place", self._widget, *possibly_relative_values_dict
        )
