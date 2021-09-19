from __future__ import annotations

from typing import Any, Callable, Dict, Literal, Optional, Tuple, Union

from ._constants import AnchorAnnotation
from ._misc import ScreenDistance
from ._utils import py_to_tcl_arguments, reversed_dict

HorAlignAlias = Optional[Literal["left", "right", "stretch"]]
MrgnAlias = Optional[Union[int, Tuple[int, ...]]]
ScrDstAlias = Optional[Union[int, str, ScreenDistance]]
ScrDstRtrnAlias = Dict[str, Union[float, ScreenDistance]]
VertAlignAlias = Optional[Literal["bottom", "stretch", "top"]]

StickyValues: dict[tuple[HorAlignAlias, VertAlignAlias], str] = {
    ("left", "bottom"): "sw",
    ("left", "stretch"): "nsw",
    ("left", "top"): "nw",
    ("left", None): "w",
    ("right", "bottom"): "es",
    ("right", "stretch"): "nes",
    ("right", "top"): "ne",
    ("right", None): "e",
    ("stretch", "bottom"): "esw",
    ("stretch", "stretch"): "nesw",
    ("stretch", "top"): "new",
    ("stretch", None): "ew",
    (None, "bottom"): "s",
    (None, "stretch"): "ns",
    (None, "top"): "n",
    (None, None): "",
}


class GridCells:
    _widget: "TukaanWidget"
    cell_managed_widgets: dict["BaseWidget", str] = {}

    @property
    def grid_cells(self) -> list[list[str]]:
        return self._grid_cells

    @grid_cells.setter
    def grid_cells(self, cells_data: list[list[str]]) -> None:
        self._grid_cells = cells_data
        self._grid_cells_values = self.__parse_grid_areas(cells_data)

        for widget in self.cell_managed_widgets.keys():
            widget.layout._set_cell(self.cell_managed_widgets[widget])

    def __parse_grid_areas(self, areas_list: list[list[str]]) -> dict[str, int]:
        result = {}
        for row_index, row_list in enumerate(areas_list):
            for col_index, cell_name in enumerate(row_list):
                if cell_name is None:
                    continue
                if cell_name in result:
                    if not result[cell_name].get("cols_counted", False):
                        result[cell_name]["colspan"] = row_list.count(cell_name)
                        result[cell_name]["cols_counted"] = True

                    if not result[cell_name].get("rows_counted", False):
                        result[cell_name]["rowspan"] = sum(
                            cell_name in item for item in areas_list
                        )
                        result[cell_name]["rows_counted"] = True
                else:
                    result[cell_name] = {
                        "row": row_index,
                        "col": col_index,
                        "rowspan": 1,
                        "colspan": 1,
                    }
        for value in result.values():
            value.pop("cols_counted", "")
            value.pop("rows_counted", "")

        return result


class GridTemplates:
    _widget: "TukaanWidget"

    @property
    def grid_row_template(self) -> tuple[int, ...]:
        return self._row_template

    @grid_row_template.setter
    def grid_row_template(self, new_row_template) -> None:
        self._row_template = new_row_template
        for index, weight in enumerate(new_row_template):
            self._widget._tcl_call(
                None, "grid", "rowconfigure", self._widget, index, "-weight", weight
            )

    @property
    def grid_col_template(self) -> tuple[int, ...]:
        return self._col_template

    @grid_col_template.setter
    def grid_col_template(self, new_col_template) -> None:
        self._col_template = new_col_template
        for index, weight in enumerate(new_col_template):
            self._widget._tcl_call(
                None, "grid", "columnconfigure", self._widget, index, "-weight", weight
            )


class Grid:
    _widget: "BaseWidget"
    manager: Callable
    cell_managed_widgets: dict["BaseWidget", str]

    def grid(
        self,
        cell: Optional[str] = None,
        col: Optional[int] = None,
        colspan: Optional[int] = None,
        hor_align: HorAlignAlias = None,
        margin: MrgnAlias = None,
        row: Optional[int] = None,
        rowspan: Optional[int] = None,
        vert_align: VertAlignAlias = None,
    ) -> None:
        padx, pady = self.__parse_margin(margin)

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
                sticky=self.__parse_sticky_values(hor_align, vert_align),
            ),
        )
        if cell:
            self._set_cell(cell)

    def _set_cell(self, cell: str) -> None:
        try:
            row = self._widget.parent.layout._grid_cells_values[cell]["row"]
            col = self._widget.parent.layout._grid_cells_values[cell]["col"]
            rowspan = self._widget.parent.layout._grid_cells_values[cell]["rowspan"]
            colspan = self._widget.parent.layout._grid_cells_values[cell]["colspan"]
        except KeyError:
            raise RuntimeError(f"cell {cell!r} doesn't exists")
        self.config(row=row, column=col, rowspan=rowspan, columnspan=colspan)

        self.cell_managed_widgets[self._widget] = cell

    def __parse_margin(
        self, to_parse
    ) -> tuple[tuple[int, ...], ...] | tuple[None, ...]:
        if isinstance(to_parse, int):
            return ((to_parse,) * 2,) * 2

        elif isinstance(to_parse, tuple) and len(to_parse) == 2:
            return ((to_parse[1], to_parse[1]), (to_parse[0],) * 2)

        elif isinstance(to_parse, tuple) and len(to_parse) == 3:
            return ((to_parse[1],) * 2, (to_parse[0], to_parse[2]))

        elif isinstance(to_parse, tuple) and len(to_parse) == 4:
            return ((to_parse[3], to_parse[1]), (to_parse[0], to_parse[2]))

        return None, None

    def __parse_sticky_values(self, hor: HorAlignAlias, vert: VertAlignAlias) -> str:
        return StickyValues[(hor, vert)]

    def __grid_info(self):
        return self._widget._tcl_call(
            {
                "-column": int,
                "-columnspan": int,
                "-row": int,
                "-rowspan": int,
                "-sticky": str,
            },
            "grid",
            "info",
            self._widget,
        )

    def config(self, **kwargs) -> None:
        # FIXME: sticky and margin values
        self._widget._tcl_call(
            None, "grid", "configure", self._widget, *py_to_tcl_arguments(**kwargs)
        )

    def __get_grid_properties(self, what: str):
        if self.manager == "grid":
            return self.__grid_info()[f"-{what}"]
        else:
            raise RuntimeError(
                f"{self._widget} is managed by position, not grid. Can't get {what}"
            )

    def __set_grid_properties(self, key: str, value: Any) -> None:
        if self.manager == "grid":
            return self.config(**{key: value})
        else:
            raise RuntimeError(
                f"{self._widget} is managed by position, not grid. Can't set {key}"
            )

    def __get_sticky_values(self, key: str) -> tuple[HorAlignAlias, VertAlignAlias]:
        return reversed_dict(StickyValues)[key]

    @property
    def cell(self) -> str:
        return self.cell_managed_widgets[self._widget]

    @cell.setter
    def cell(self, new_cell: str) -> None:
        self._set_cell(new_cell)

    @property
    def row(self) -> int:
        return self.__get_grid_properties("row")

    @row.setter
    def row(self, new_row: int) -> None:
        self.__set_grid_properties("row", new_row)

    @property
    def col(self) -> int:
        return self.__get_grid_properties("column")

    @col.setter
    def col(self, new_col: int) -> None:
        self.__set_grid_properties("column", new_col)

    @property
    def rowspan(self) -> int:
        return self.__get_grid_properties("rowspan")

    @rowspan.setter
    def rowspan(self, new_rowspan: int) -> None:
        self.__set_grid_properties("rowspan", new_rowspan)

    @property
    def colspan(self) -> int:
        return self.__get_grid_properties("columnspan")

    @colspan.setter
    def colspan(self, new_colspan: int) -> None:
        self.__set_grid_properties("columnspan", new_colspan)

    @property
    def hor_align(self) -> HorAlignAlias:
        return self.__get_sticky_values(self.__get_grid_properties("sticky"))[0]

    @hor_align.setter
    def hor_align(self, new_hor_align: HorAlignAlias) -> None:
        self.__set_grid_properties(
            "sticky", self.__parse_sticky_values(new_hor_align, self.vert_align)
        )

    @property
    def vert_align(self) -> VertAlignAlias:
        return self.__get_sticky_values(self.__get_grid_properties("sticky"))[1]

    @vert_align.setter
    def vert_align(self, new_vert_align: VertAlignAlias) -> None:
        self.__set_grid_properties(
            "sticky", self.__parse_sticky_values(self.hor_align, new_vert_align)
        )

    @property
    def margin(self) -> tuple[int, ...]:
        result = self._widget._tcl_call({}, "grid", "info", self._widget)

        padx = tuple(map(int, result["-padx"].split(" ")))
        pady = tuple(map(int, result["-pady"].split(" ")))

        margin = [i if len(i) == 2 else i * 2 for i in (padx, pady)]

        return margin[1][0], margin[0][1], margin[1][1], margin[0][0]

    @margin.setter
    def margin(self, new_margin: MrgnAlias) -> None:  # type: ignore
        result = self.__parse_margin(new_margin)
        self.__set_grid_properties("padx", result[0])
        self.__set_grid_properties("pady", result[1])


class Position:
    _widget: "BaseWidget"
    manager: Callable

    def position(
        self,
        anchor: AnchorAnnotation = None,
        height: ScrDstAlias = None,
        width: ScrDstAlias = None,
        x: ScrDstAlias = None,
        y: ScrDstAlias = None,
    ) -> None:
        possibly_relative_values_dict = self.__parse_possibly_relative_values(
            ("x", "y", "width", "height"), (x, y, width, height)
        )

        self._widget._tcl_call(
            None,
            "place",
            self._widget,
            *py_to_tcl_arguments(**possibly_relative_values_dict, anchor=anchor),
        )

    def __parse_possibly_relative_values(
        self, names: tuple[str, ...], values: tuple[ScrDstAlias, ...]
    ) -> ScrDstRtrnAlias:
        result_dict: ScrDstRtrnAlias = {}

        for name, value in zip(names, values):
            if value is None:
                continue
            elif isinstance(value, str) and value.endswith("%"):
                result_dict[f"rel{name}"] = float(value[:-1]) / 100
            elif isinstance(value, (int, ScreenDistance)):
                result_dict[name] = value
            else:
                raise TypeError(f"expected {ScrDstAlias}, got {type(value)}")

        return result_dict


class LayoutManager(Grid, Position, GridCells, GridTemplates):
    def __init__(self, widget):
        self._widget = widget

    @property
    def manager(self):
        result = self._widget._tcl_call(str, "winfo", "manager", self._widget)
        if result == "place":
            return "position"
        return result


class WindowLayoutManager(GridCells, GridTemplates):
    def __init__(self, widget):
        self._widget = widget
