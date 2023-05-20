from __future__ import annotations

import collections
from typing import TYPE_CHECKING, Any, Iterator, Optional, Tuple, Union

from tukaan._tcl import Tcl
from tukaan._typing import T
from tukaan.enums import Align
from tukaan.errors import WrongWidgetError
from tukaan.layouts.base import LayoutManagerBase

if TYPE_CHECKING:
    from tukaan._base import Widget

AlignOrNone = Optional[Align]
TukaanMargin = Optional[Union[Tuple[int, ...], int]]
TkPad = Union[Tuple[Tuple[int, int], Tuple[int, int]], Tuple[None, None]]

VERT_ALIGN = {Align.Start: "n", Align.End: "s", Align.Stretch: "ns"}
HOR_ALIGN = {Align.Start: "w", Align.End: "e", Align.Stretch: "ew"}


def convert_align_to_tk_sticky(align: AlignOrNone | tuple[AlignOrNone, AlignOrNone]) -> str:
    if not align or align in (Align.Center, (Align.Center, Align.Center), (None, None)):
        return ""

    if isinstance(align, tuple):
        if len(align) == 1:
            align = align * 2
    elif isinstance(align, Align):
        align = (align,) * 2
    else:
        raise TypeError

    tk_align = ""
    tk_align += VERT_ALIGN.get(align[1], "")
    tk_align += HOR_ALIGN.get(align[0], "")

    return tk_align


def convert_margin_to_tk_pad(margin: TukaanMargin) -> TkPad:
    if isinstance(margin, int):
        return (margin, margin), (margin, margin)
    elif isinstance(margin, tuple):
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


class GridRowsCols:
    _indices: tuple[int]

    def __init__(self, owner_name: str, type_: str) -> None:
        self._owner_name = owner_name
        self._type = type_

    def __getitem__(self, index):
        if index is ... or index == slice(None):
            self._indices = ("all",)
        elif isinstance(index, int):
            self._indices = (index,)
        elif isinstance(index, tuple):
            self._indices = index
        elif isinstance(index, slice):
            self._indices = tuple(range(index.start or 0, index.stop or len(self), index.step or 1))
        else:
            raise TypeError(f"invalid {self._type} index: {index!r}")
        return self

    def __len__(self) -> int:
        return Tcl.call((int,), "grid", "size", self._owner_name)[self._type == "column"]

    @property
    def weight(self) -> int | None | tuple[int | None, ...]:
        if self._indices == ("all",):
            indices: tuple | range = range(len(self))
        else:
            indices = self._indices

        result: list[int | None] = []
        for index in indices:
            result.append(
                Tcl.eval(int, f"grid {self._type}configure {self._owner_name} {index} -weight")
                or None
            )

        return result[0] if len(result) == 1 else tuple(result)

    @weight.setter
    def weight(self, value: int) -> None:
        Tcl.call(
            None,
            "grid",
            f"{self._type}configure",
            self._owner_name,
            self._indices,
            "-weight",
            value or 0,
        )

    @property
    def minsize(self) -> int | None | tuple[int | None, ...]:
        if self._indices == ("all",):
            indices: tuple | range = range(len(self))
        else:
            indices = self._indices

        result: list[int | None] = []
        for index in indices:
            result.append(
                Tcl.eval(int, f"grid {self._type}configure {self._owner_name} {index} -minsize")
                or None
            )

        return result[0] if len(result) == 1 else tuple(result)

    @minsize.setter
    def minsize(self, value: int) -> None:
        Tcl.call(
            None,
            "grid",
            f"{self._type}configure",
            self._owner_name,
            self._indices,
            "-minsize",
            value or 0,
        )


class GridLayoutManager(LayoutManagerBase, name="grid"):
    def __call__(
        self,
        row: int | None = None,
        col: int | None = None,
        *,
        align: tuple[AlignOrNone, AlignOrNone] | AlignOrNone = None,
        cell: str | None = None,
        colspan: int | None = None,
        margin: TukaanMargin = None,
        rowspan: int | None = None,
    ) -> None:
        sticky = convert_align_to_tk_sticky(align)
        padx, pady = convert_margin_to_tk_pad(margin)

        Tcl.call(
            None,
            "grid",
            "configure",
            self._owner_toplevel_name,
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

    def _query_option(self, return_type: type[T], option: str) -> T:
        return Tcl.call({option: return_type}, "grid", "info", self._owner_toplevel_name)[option]

    def _configure(self, **kwargs: Any) -> None:
        Tcl.call(None, "grid", "configure", self._owner_toplevel_name, *Tcl.to_tcl_args(**kwargs))

    def detect(self, x: int, y: int) -> tuple[int, int]:
        return tuple(reversed(Tcl.call((int,), "grid", "location", self._owner_name, x, y)))

    def hide(self) -> None:
        Tcl.call(None, "grid", "remove", self._owner_toplevel_name)

    def unhide(self) -> None:
        Tcl.call(None, "grid", "configure", self._owner_toplevel_name)

    def hide_children(self, child: Widget, *more) -> None:
        children = (i._toplevel_name for i in more + (child,))

        if child._name is self._owner_name or self._owner_name in children:
            raise WrongWidgetError(
                "widget is not a children of itself. Use `widget.grid.hide` instead to hide it."
            )
        Tcl.call(None, "grid", "remove", *children)

    def unhide_children(self, child: Widget, *more) -> None:
        children = (i._toplevel_name for i in more + (child,))

        if child._name is self._owner_name or self._owner_name in children:
            raise WrongWidgetError(
                "widget is not a children of itself. Use `widget.grid.unhide` instead to unhide it."
            )
        Tcl.call(None, "grid", *children)

    def delete_children(self, child: Widget, *more) -> None:
        children = (i._toplevel_name for i in more + (child,))

        if child._name is self._owner_name or self._owner_name in children:
            raise WrongWidgetError("can't delete widget from itself.")
        Tcl.call(None, "grid", "forget", *children)

    @property
    def children(self) -> Iterator[Widget]:
        from tukaan._base import Widget

        for child in Tcl.call((str,), "grid", "slaves", self._owner_name):
            yield Tcl.from_(Widget, child)

    @property
    def size(self) -> tuple[int, int]:
        return Tcl.call((int,), "grid", "size", self._owner_name)

    @property
    def location(self) -> tuple[int | None, int | None]:
        return self._query_option(int, "-row"), self._query_option(int, "-column")

    @location.setter
    def location(self, value: tuple[int, int]) -> None:
        row, col = value
        self._configure(row=row, column=col)

    @property
    def row(self) -> int | None:
        return self._query_option(int, "-row")

    @row.setter
    def row(self, value: int) -> None:
        self._configure(row=value)

    @property
    def col(self) -> int | None:
        return self._query_option(int, "-column")

    @col.setter
    def col(self, value: int) -> None:
        self._configure(column=value)

    @property
    def rowspan(self) -> int | None:
        return self._query_option(int, "-rowspan")

    @rowspan.setter
    def rowspan(self, value: int) -> None:
        self._configure(rowspan=value)

    @property
    def colspan(self) -> int | None:
        return self._query_option(int, "-columnspan")

    @colspan.setter
    def colspan(self, value: int) -> None:
        self._configure(columnspan=value)

    @property
    def margin(self) -> tuple[int, ...]:
        result: dict[str, tuple[int, ...]] = Tcl.call(
            {"-padx": (int,), "-pady": (int,)}, "grid", "info", self._owner_toplevel_name
        )

        x, y = result["-padx"], result["-pady"]
        (left, right) = x if len(x) == 2 else x * 2
        (top, bottom) = y if len(y) == 2 else y * 2

        return top, right, bottom, left

    @margin.setter
    def margin(self, value: TukaanMargin) -> None:
        padx, pady = convert_margin_to_tk_pad(value)
        self._configure(padx=padx, pady=pady)

    @property
    def align(self) -> tuple[AlignOrNone, AlignOrNone]:
        hor = vert = Align.Center
        sticky = set(self._query_option(str, "-sticky"))

        if sticky & {"w", "e"} == {"w", "e"}:
            hor = Align.Stretch
        elif "w" in sticky:
            hor = Align.Start
        elif "e" in sticky:
            hor = Align.End

        if sticky & {"n", "s"} == {"n", "s"}:
            vert = Align.Stretch
        elif "n" in sticky:
            vert = Align.Start
        elif "s" in sticky:
            vert = Align.End

        return hor, vert

    @align.setter
    def align(self, value: tuple[AlignOrNone, AlignOrNone] | None) -> None:
        self._configure(sticky=convert_align_to_tk_sticky(value))

    @property
    def propagate(self) -> bool:
        return Tcl.call(bool, "grid", "propagate", self._owner_toplevel_name)

    @propagate.setter
    def propagate(self, value: bool) -> None:
        Tcl.call(bool, "grid", "propagate", self._owner_toplevel_name, value)

    @property
    def rows(self) -> GridRowsCols:
        return GridRowsCols(self._owner_name, "row")

    @property
    def cols(self) -> GridRowsCols:
        return GridRowsCols(self._owner_name, "column")
