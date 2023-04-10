from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from tukaan._tcl import Tcl
from tukaan.enums import Align
from tukaan.exceptions import LayoutError

if TYPE_CHECKING:
    from tukaan._base import ToplevelBase, WidgetBase

IntOrStr = TypeVar("IntOrStr", int, str)


class LayoutManager(ABC):
    _type: str

    def __init__(self, owner: WidgetBase) -> None:
        self._widget = owner

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _cget(self, return_type: type[IntOrStr], option: str) -> IntOrStr | None:
        try:
            result = Tcl.call({option: return_type}, self._type, "info", self._widget)[option]
        except KeyError:
            return None
        else:
            return result

    def _config(self, **kwargs: Any) -> None:
        Tcl.call(None, self._type, "configure", self._widget, *Tcl.to_tcl_args(**kwargs))


class Grid(LayoutManager):
    _type = "grid"

    def __call__(
        self,
        row: int | None = None,
        col: int | None = None,
        *,
        align: tuple[Align | None, Align | None] | None = None,
        cell: str | None = None,
        colspan: int | None = None,
        margin: int | tuple[int, ...] | None = None,
        rowspan: int | None = None,
    ) -> None:
        sticky = self._parse_align(align)
        padx, pady = self._parse_margin(margin)

        if cell:
            self._set_cell(cell)
            row = col = rowspan = colspan = None

        Tcl.call(
            None,
            "grid",
            "configure",
            self._widget._lm_path,
            *Tcl.to_tcl_args(
                row=row,
                column=col,
                rowspan=rowspan,
                columnspan=colspan,
                sticky=sticky,
                padx=padx,
                pady=pady,
            ),
        )

    def _set_cell(self, cell_name: str) -> None:
        try:
            cell = self._widget.parent.grid._cells_values[cell_name]
        except KeyError:
            raise LayoutError(f"cell {cell_name!r} doesn't exists") from None

        Tcl.call(
            None,
            "grid",
            "configure",
            self._widget,
            *Tcl.to_tcl_args(
                row=cell["row"],
                column=cell["col"],
                rowspan=cell["rowspan"],
                columnspan=cell["colspan"],
            ),
        )

        self._widget.parent.grid._cell_managed_children[self._widget] = cell_name

    def _parse_align(self, align: tuple[Align | None, Align | None] | None) -> str:
        if align is None or align == (None, None):
            return ""

        result = ""

        if isinstance(align, (tuple, list)) and len(align) == 1:
            align = align * 2
        elif isinstance(align, Align):
            align = (align,) * 2

        hor, vert = align

        if vert is Align.Start:
            result += "n"
        elif vert is Align.End:
            result += "s"
        elif vert is Align.Stretch:
            result += "ns"

        if hor is Align.Start:
            result += "w"
        elif hor is Align.End:
            result += "e"
        elif hor is Align.Stretch:
            result += "ew"

        return result

    def _parse_margin(
        self, margin: int | tuple[int, ...] | None
    ) -> tuple[tuple[int, int], tuple[int, int]] | tuple[None, None]:
        if isinstance(margin, int):
            return ((margin,) * 2,) * 2
        elif isinstance(margin, (tuple, list)):
            length = len(margin)

            if length == 2:
                vert, hor = margin
                return (hor,) * 2, (vert,) * 2
            elif length == 3:
                top, hor, bottom = margin
                return (hor,) * 2, (top, bottom)
            elif length == 4:
                top, right, bottom, left = margin
                return (left, right), (top, bottom)

        return None, None

    def _get_pad(self):
        result = Tcl.call(
            {
                "-padx": (int,),
                "-pady": (int,),
            },
            "grid",
            "info",
            self._widget,
        )
        return result["-padx"], result["-pady"]

    @property
    def location(self) -> tuple[int | None, int | None]:
        return self._cget(int, "-row"), self._cget(int, "-column")

    @location.setter
    def location(self, value: tuple[int, int]) -> None:
        row, col = value
        self._config(row=row, col=col)

    @property
    def row(self) -> int | None:
        return self._cget(int, "-row")

    @row.setter
    def row(self, value: int) -> None:
        self._config(row=value)

    @property
    def col(self) -> int | None:
        return self._cget(int, "-column")

    @col.setter
    def col(self, value: int) -> None:
        self._config(column=value)

    @property
    def rowspan(self) -> int | None:
        return self._cget(int, "-rowspan")

    @rowspan.setter
    def rowspan(self, value: int) -> None:
        self._config(rowspan=value)

    @property
    def colspan(self) -> int | None:
        return self._cget(int, "-columnspan")

    @colspan.setter
    def colspan(self, value: int) -> None:
        self._config(columnspan=value)

    @property
    def cell(self) -> str | None:
        try:
            return self._widget.parent.grid._cell_managed_children[self._widget]
        except KeyError:
            return None

    @cell.setter
    def cell(self, value: str) -> None:
        self._set_cell(value)

    @property
    def margin(self) -> tuple[int, ...]:
        (left, right), (top, bottom) = (x if len(x) == 2 else x * 2 for x in self._get_pad())
        return top, right, bottom, left

    @margin.setter
    def margin(self, value: tuple[int, ...]) -> None:
        padx, pady = self._parse_margin(value)
        self._config(padx=padx, pady=pady)

    @property
    def align(self) -> tuple[Align | None, Align | None]:
        h = v = None
        sticky = set(self._cget(str, "-sticky"))

        if sticky & {"w", "e"} == {"w", "e"}:
            h = Align.Stretch
        elif "w" in sticky:
            h = Align.Start
        elif "e" in sticky:
            h = Align.End

        if sticky & {"n", "s"} == {"n", "s"}:
            v = Align.Stretch
        elif "n" in sticky:
            v = Align.Start
        elif "s" in sticky:
            v = Align.End

        return h, v

    @align.setter
    def align(self, value: tuple[Align | None, Align | None] | None) -> None:
        self._config(sticky=self._parse_align(value))


class GridCells:
    @staticmethod
    def _parse(cells_list: list[list[str | None]]):
        result: dict[str, dict[str, int | bool]] = {}

        for row_index, row_list in enumerate(cells_list):
            for col_index, cell_name in enumerate(row_list):
                if cell_name is None:
                    continue
                if cell_name in result:
                    if not result[cell_name].get("cols_counted", False):
                        result[cell_name]["colspan"] = row_list.count(cell_name)
                        result[cell_name]["cols_counted"] = True

                    if not result[cell_name].get("rows_counted", False):
                        result[cell_name]["rowspan"] = sum(cell_name in item for item in cells_list)
                        result[cell_name]["rows_counted"] = True
                else:
                    result[cell_name] = {
                        "row": row_index,
                        "col": col_index,
                        "rowspan": 1,  # reset to 1 when modifying the cell layout
                        "colspan": 1,
                    }

        return result

    @staticmethod
    def _update(owner):
        for widget, cell in owner.grid._cell_managed_children.items():
            widget.grid._set_cell(cell)  # _set_cell does the update

    def __set__(self, obj, value: list[list[str | None]]) -> None:
        obj._cells = value
        obj._cells_values = GridCells._parse(value)
        GridCells._update(obj._widget)

    def __get__(self, obj, *_) -> list[list[str | None]]:
        return obj._cells


class ToplevelGrid:
    # TODO: row/col weight
    # TODO: row/col gap

    _cells = []
    _cells_values = {}
    _cell_managed_children = {}

    cells = GridCells()

    def __init__(self, owner: ToplevelBase) -> None:
        self._widget = owner

    @property
    def size(self) -> tuple[int, int]:
        return Tcl.call((int,), "grid", "size", self._widget)

    def detect(self, x: int, y: int):
        return tuple(reversed(Tcl.call((int,), "grid", "location", self._widget, x, y)))


class ContainerGrid(Grid, ToplevelGrid):
    ...
