from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, TypeVar

from tukaan.layouts.base import LayoutManagerBase

if TYPE_CHECKING:
    from tukaan._base import WidgetBase

from tukaan._tcl import Tcl
from tukaan.enums import Align

AlignOrNone = TypeVar("AlignOrNone", Align, None)
TukaanMargin = TypeVar("MarginOrNone", tuple[int, ...], int, None)
TkPad = TypeVar("TkPad", tuple[tuple[int, int], tuple[int, int]], tuple[None, None])

VERT_ALIGN = {Align.Start: "n", Align.End: "s", Align.Stretch: "ns"}
HOR_ALIGN = {Align.Start: "w", Align.End: "e", Align.Stretch: "ew"}


def convert_align_to_tk_sticky(align: tuple[AlignOrNone, AlignOrNone] | None) -> str:
    if align is None or align == (None, None):
        return ""

    if isinstance(align, tuple) and len(align) == 1:
        align = align * 2
    elif isinstance(align, Align):
        align = (align,) * 2

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


class GridLayoutManager(LayoutManagerBase, name="grid"):
    def _query_option(self, return_type: type[int | str], option: str) -> int | str | None:
        try:
            result = Tcl.call({option: return_type}, "grid", "info", self._owner)[option]
        except KeyError:
            return None
        else:
            return result

    def _configure(self, **kwargs: Any) -> None:
        Tcl.call(None, "grid", "configure", self._owner, *Tcl.to_tcl_args(**kwargs))

    def __call__(
        self,
        row: int | None = None,
        col: int | None = None,
        *,
        align: tuple[AlignOrNone, AlignOrNone] | None = None,
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
            self._owner._lm_path,
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

    def detect(self, x: int, y: int) -> tuple[int, int]:
        return tuple(reversed(Tcl.call((int,), "grid", "location", self._owner._lm_path, x, y)))

    def hide(self) -> None:
        Tcl.call(None, "grid", "remove", self._owner._lm_path)

    def unhide(self) -> None:
        Tcl.call(None, "grid", "configure", self._owner._lm_path)

    def hide_children(self, *children) -> None:
        Tcl.call(None, "grid", "remove", *{child._lm_path for child in children})

    def unhide_children(self, *children) -> None:
        Tcl.call(None, "grid", "configure", *{child._lm_path for child in children})

    def delete_children(self, *children) -> None:
        Tcl.call(None, "grid", "forget", *{child._lm_path for child in children})

    @property
    def children(self) -> Iterator[WidgetBase]:
        from tukaan._base import WidgetBase

        for child in Tcl.call([WidgetBase], "grid", "slaves", self._owner._lm_path):
            yield child

    @property
    def size(self) -> tuple[int, int]:
        return Tcl.call((int,), "grid", "size", self._owner._lm_path)

    @property
    def location(self) -> tuple[int | None, int | None]:
        return self._query_option(int, "-row"), self._query_option(int, "-column")

    @location.setter
    def location(self, value: tuple[int, int]) -> None:
        row, col = value
        self._configure(row=row, column=col)

    @property
    def cell(self) -> str | None:
        ...

    @cell.setter
    def cell(self, value: str) -> None:
        ...

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
        result = Tcl.call({"-padx": (int,), "-pady": (int,)}, "grid", "info", self._owner)

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
        hor = vert = None
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
        return Tcl.call(bool, "grid", "propagate", self._owner._lm_path)

    @propagate.setter
    def propagate(self, value: bool) -> None:
        Tcl.call(bool, "grid", "propagate", self._owner._lm_path, value)
