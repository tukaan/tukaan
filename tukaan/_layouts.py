from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Literal, Optional, Tuple, Union

if TYPE_CHECKING:
    # pyright won't complain
    from ._base import TkWidget

from ._constants import AnchorAnnotation
from ._misc import ScreenDistance
from ._utils import py_to_tcl_arguments
from .exceptions import CellNotFoundError, LayoutError

HorAlignAlias = Optional[Literal["left", "right", "stretch"]]
MrgnAlias = Optional[Union[int, Tuple[int, ...]]]
ScrDstAlias = Optional[Union[int, str, ScreenDistance]]
ScrDstRtrnAlias = Dict[str, Union[float, ScreenDistance]]
VertAlignAlias = Optional[Literal["bottom", "stretch", "top"]]


class StickyValues(enum.Enum):
    SW = ("left", "bottom")
    NSW = ("left", "stretch")
    NW = ("left", "top")
    W = ("left", None)
    ES = ("right", "bottom")
    NES = ("right", "stretch")
    NE = ("right", "top")
    E = ("right", None)
    ESW = ("stretch", "bottom")
    NESW = ("stretch", "stretch")
    NEW = ("stretch", "top")
    EW = ("stretch", None)
    S = (None, "bottom")
    NS = (None, "stretch")
    N = (None, "top")
    NONE = (None, None)


class GridCells:
    _widget: TkWidget
    _grid_cells: list[list[str]]
    _cell_managed_children: dict[TkWidget, str]

    def set_grid_cells(self, cells_data: list[list[str]]) -> None:
        self._grid_cells = cells_data
        self._grid_cells_values = self._parse_grid_cells(cells_data)

        for widget in self._cell_managed_children.keys():
            widget.layout._set_cell(self._cell_managed_children[widget])

    @property
    def grid_cells(self) -> list[list[str]]:
        return self._grid_cells

    @grid_cells.setter
    def grid_cells(self, cells_data: list[list[str]]) -> None:
        self.set_grid_cells(cells_data)

    def _parse_grid_cells(
        self, areas_list: list[list[str]]
    ) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int | bool]] = {}
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
    _widget: TkWidget
    _row_template: tuple
    _col_template: tuple

    def _grid_or_col_template(
        self, which: str, template: int | tuple[int, ...]
    ) -> None:
        attr, command = {
            "row": ("_row_template", "rowconfigure"),
            "col": ("_col_template", "columnconfigure"),
        }[which]

        if isinstance(template, int):
            template = (template,)

        setattr(self, attr, template)
        for index, weight in enumerate(template):
            self._widget._tcl_call(
                None, "grid", command, self._widget, index, "-weight", weight
            )

    @property
    def grid_row_template(self) -> tuple[int, ...]:
        return self._row_template

    @grid_row_template.setter
    def grid_row_template(self, new_row_template: int | tuple[int, ...]) -> None:
        self._grid_or_col_template("row", new_row_template)

    @property
    def grid_col_template(self) -> tuple[int, ...]:
        return self._col_template

    @grid_col_template.setter
    def grid_col_template(self, new_col_template: int | tuple[int, ...]) -> None:
        self._grid_or_col_template("col", new_col_template)


class Grid:
    _widget: TkWidget
    _cell_managed_children: dict[TkWidget, str]
    _get_lm_properties: Callable[[Grid, str], Any]
    _set_lm_properties: Callable[[Grid, str, str, Any], None]
    _info: Callable

    def grid(
        self,
        align: tuple[HorAlignAlias, VertAlignAlias]
        | HorAlignAlias
        | VertAlignAlias = None,
        cell: Optional[str] = None,
        col: Optional[int] = None,
        colspan: Optional[int] = None,
        hor_align: HorAlignAlias = None,
        margin: MrgnAlias = None,
        row: Optional[int] = None,
        rowspan: Optional[int] = None,
        vert_align: VertAlignAlias = None,
    ) -> None:
        padx, pady = self._parse_margin(margin)

        if align and not any((hor_align, vert_align)):
            hor_align, vert_align = (align,) * 2  # type: ignore
        elif align:
            raise LayoutError("both align and hor_align and/or vert_align given")

        self._widget._tcl_call(
            None,
            "grid",
            "configure",
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
        if cell:
            self._set_cell(cell)

        self._real_manager = "grid"

    def _set_cell(self, cell: str) -> None:
        try:
            row = self._widget.parent.layout._grid_cells_values[cell]["row"]
            col = self._widget.parent.layout._grid_cells_values[cell]["col"]
            rowspan = self._widget.parent.layout._grid_cells_values[cell]["rowspan"]
            colspan = self._widget.parent.layout._grid_cells_values[cell]["colspan"]
        except KeyError:
            raise CellNotFoundError(f"cell {cell!r} doesn't exists")
        except AttributeError:
            raise CellNotFoundError(f"{self._widget.parent} has no cell layout set up")
        self._widget._tcl_call(
            None,
            "grid",
            "configure",
            self._widget,
            *py_to_tcl_arguments(
                row=row, column=col, rowspan=rowspan, columnspan=colspan
            ),
        )

        self._widget.parent.layout._cell_managed_children[self._widget] = cell

    def _parse_margin(self, to_parse) -> tuple[tuple[int, ...], ...] | tuple[None, ...]:
        if isinstance(to_parse, int):
            return ((to_parse,) * 2,) * 2

        elif isinstance(to_parse, tuple) and len(to_parse) == 2:
            return (to_parse[1], to_parse[1]), (to_parse[0],) * 2

        elif isinstance(to_parse, tuple) and len(to_parse) == 3:
            return (to_parse[1],) * 2, (to_parse[0], to_parse[2])

        elif isinstance(to_parse, tuple) and len(to_parse) == 4:
            return (to_parse[3], to_parse[1]), (to_parse[0], to_parse[2])

        return None, None

    def _parse_sticky_values(self, hor: HorAlignAlias, vert: VertAlignAlias) -> str:
        try:
            result = StickyValues((hor, vert)).name.lower()
            return "" if result == "none" else result
        except KeyError:
            raise LayoutError(f"invalid alignment value: {(hor, vert)}")

    def _get_sticky_values(self, key: str) -> tuple[HorAlignAlias, VertAlignAlias]:
        if key == "":
            key = "NONE"
        return StickyValues[key].value

    @property
    def cell(self) -> str | None:
        try:
            return self._widget.parent.layout._cell_managed_children[self._widget]
        except KeyError:
            return None

    @cell.setter
    def cell(self, new_cell: str) -> None:
        self._set_cell(new_cell)

    @property
    def row(self) -> int:
        return self._get_lm_properties("row")

    @row.setter
    def row(self, new_row: int) -> None:
        self._set_lm_properties("grid", "row", new_row)

    @property
    def col(self) -> int:
        return self._get_lm_properties("column")

    @col.setter
    def col(self, new_col: int) -> None:
        self._set_lm_properties("grid", "column", new_col)

    @property
    def rowspan(self) -> int:
        return self._get_lm_properties("rowspan")

    @rowspan.setter
    def rowspan(self, new_rowspan: int) -> None:
        self._set_lm_properties("grid", "rowspan", new_rowspan)

    @property
    def colspan(self) -> int:
        return self._get_lm_properties("columnspan")

    @colspan.setter
    def colspan(self, new_colspan: int) -> None:
        self._set_lm_properties("grid", "columnspan", new_colspan)

    @property
    def hor_align(self) -> HorAlignAlias:
        return self._get_sticky_values(self._get_lm_properties("sticky"))[0]

    @hor_align.setter
    def hor_align(self, new_hor_align: HorAlignAlias) -> None:
        self._set_lm_properties(
            "grid", "sticky", self._parse_sticky_values(new_hor_align, self.vert_align)
        )

    @property
    def vert_align(self) -> VertAlignAlias:
        return self._get_sticky_values(self._get_lm_properties("sticky"))[1]

    @vert_align.setter
    def vert_align(self, new_vert_align: VertAlignAlias) -> None:
        self._set_lm_properties(
            "grid", "sticky", self._parse_sticky_values(self.hor_align, new_vert_align)
        )

    @property
    def align(self):
        return self._get_sticky_values(self._get_lm_properties("sticky"))

    @align.setter
    def align(
        self,
        new_alignment: tuple[HorAlignAlias, VertAlignAlias]
        | HorAlignAlias
        | VertAlignAlias,
    ):
        if not isinstance(new_alignment, tuple):
            new_alignment = (new_alignment,) * 2  # type: ignore
        self._set_lm_properties(
            "grid", "sticky", self._parse_sticky_values(*new_alignment)
        )

    @property
    def margin(self) -> tuple[int, ...]:
        result = self._info()

        padx = tuple(map(int, result["-padx"].split(" ")))
        pady = tuple(map(int, result["-pady"].split(" ")))

        margin = [elem if len(elem) == 2 else elem * 2 for elem in (padx, pady)]

        return margin[1][0], margin[0][1], margin[1][1], margin[0][0]

    @margin.setter
    def margin(self, new_margin: MrgnAlias) -> None:  # type: ignore
        result = self._parse_margin(new_margin)
        self._set_lm_properties("grid", "padx", result[0])
        self._set_lm_properties("grid", "pady", result[1])


class Position:
    _widget: TkWidget
    _get_lm_properties: Callable[[Position, str], Any]
    _set_lm_properties: Callable[[Position, str, str, Any], None]

    def position(
        self,
        anchor: AnchorAnnotation = None,
        height: ScrDstAlias = None,
        width: ScrDstAlias = None,
        x: ScrDstAlias = 0,
        y: ScrDstAlias = 0,
    ) -> None:
        possibly_relative_values_dict = self._parse_possibly_relative_values(
            ("x", "y", "width", "height"), (x, y, width, height)
        )

        self._widget._tcl_call(
            None,
            "place",
            "configure",
            self._widget,
            *py_to_tcl_arguments(**possibly_relative_values_dict, anchor=anchor),
        )

        if self._widget in self._widget.parent.layout._cell_managed_children:
            del self._widget.parent.layout._cell_managed_children[self._widget]

        self._real_manager = "place"

    def _parse_possibly_relative_values(
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
                raise ValueError(f"invalid screendistance: {value}")

        return result_dict

    @property
    def x(self) -> int:
        return self._get_lm_properties("x")

    @x.setter
    def x(self, new_x: int) -> None:
        self._set_lm_properties("place", "x", new_x)

    @property
    def y(self) -> int:
        return self._get_lm_properties("y")

    @y.setter
    def y(self, new_y: int) -> None:
        self._set_lm_properties("place", "y", new_y)

    @property
    def width(self) -> int:
        return self._get_lm_properties("width")

    @width.setter
    def width(self, new_width: int) -> None:
        self._set_lm_properties("place", "width", new_width)

    @property
    def height(self) -> int:
        return self._get_lm_properties("height")

    @height.setter
    def height(self, new_height: int) -> None:
        self._set_lm_properties("place", "height", new_height)


class BaseLayoutManager(GridCells, GridTemplates):
    def __init__(self, widget):
        self._widget = widget
        self._cell_managed_children = {}
        self._grid_cells = []


class LayoutManager(BaseLayoutManager, Grid, Position):
    _real_manager: str

    def _get_manager(self):
        return self._widget._tcl_call(str, "winfo", "manager", self._widget)

    @property
    def manager(self):
        result = self._get_manager()
        if result == "place":
            return "position"
        return result

    @manager.setter
    def manager(self, new_manager: Literal["grid", "position"]) -> None:
        try:
            self.remove()
            getattr(self, new_manager)()  # lol
        except AttributeError:
            raise LayoutError(f"invalid lyaout manager: {new_manager}")

    @property
    def propagation(self):
        lm = self._get_manager()
        if lm == "place":
            raise LayoutError("widget not managed by grid, can't get propagation")
        return self._widget._tcl_call(
            bool, self._get_manager(), "propagate", self._widget
        )

    @propagation.setter
    def propagation(self, new_propagation: bool):
        lm = self._get_manager()
        if lm == "place":
            raise LayoutError("widget not managed by grid, can't set propagation")
        self._widget._tcl_call(
            None, self._get_manager(), "propagate", self._widget, new_propagation
        )

    def remove(self):
        self._widget._tcl_call(None, self._get_manager(), "forget", self._widget)

    def move(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if value is not None:
                try:
                    value += getattr(self, key)
                except (AttributeError, KeyError):
                    raise TypeError(
                        f"move() got an unexpected keyword argument {key!r}"
                    )
                setattr(self, key, value)

    def _config(self, _lm: Literal["grid", "place"] = None, **kwargs) -> None:
        if _lm is None:
            _lm = self._get_manager()
        self._real_manager = _lm
        self._widget._tcl_call(
            None, _lm, "configure", self._widget, *py_to_tcl_arguments(**kwargs)
        )

    def _info(self):
        result = self._widget._tcl_call(
            {
                "-column": int,
                "-columnspan": int,
                "-row": int,
                "-rowspan": int,
                "-sticky": str,
                "-x": int,
                "-y": int,
                "-anchor": str,
                "-width": int,
                "-height": int,
            },
            self._get_manager(),
            "info",
            self._widget,
        )
        return {key.lstrip("-"): value for key, value in result.items()}

    def _get_lm_properties(self: Grid, what: str) -> Any:
        try:
            return self._info()[what]
        except KeyError:
            raise LayoutError(
                f"can't get {what!r}. This widget is managed by another layout manager,"
                + f" which doesn't supports {what!r}"
            )

    def _set_lm_properties(self, lm, key: str, value: Any) -> None:
        return self._config(_lm=lm, **{key: value})
