from __future__ import annotations

from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

from libtukaan import Serif

from tukaan._base import TkWidget
from tukaan._props import RWProperty, T_co, T_contra
from tukaan._tcl import Tcl
from tukaan._utils import _fonts, counts, seq_pairs
from tukaan.exceptions import FontError, TclError

from .fontfile import FontFile, TrueTypeCollection

preset_fonts = {
    "TkCaptionFont",
    "TkDefaultFont",
    "TkFixedFont",
    "TkHeadingFont",
    "TkIconFont",
    "TkMenuFont",
    "TkSmallCaptionFont",
    "TkTextFont",
    "TkTooltipFont",
}


FontMetrics = namedtuple("FontMetrics", ["ascent", "descent", "line_spacing", "fixed"])


class _FontProperty(RWProperty[T_co, T_co]):
    TYPE: type[str] | type[int] | type[bool]

    def __init__(self, option: str | None = None) -> None:
        self._option = option

    def __set_name__(self, owner: object, name: str):
        if self._option is None:
            self._option = name

    def __get__(self, instance: TkWidget, owner: object = None) -> T_co:
        if owner is None:
            return NotImplemented
        return Tcl.call(self.TYPE, "font", "actual", instance, f"-{self._option}")

    def __set__(self, instance: TkWidget, value: object):
        Tcl.call(None, "font", "configure", instance._name, f"-{self._option}", value)


class _BoolFontProperty(_FontProperty[bool]):
    TYPE = bool


class _IntFontProperty(_FontProperty[int]):
    TYPE = int


class _StrFontProperty(_FontProperty[str]):
    TYPE = str


class _FontStyleProperty(_FontProperty[bool]):
    TYPE = str
    
    def __init__(self, option: str, truthy: str, falsy: str) -> None:
        self._option = option
        self._truthy = truthy
        self._falsy = falsy

    def __get__(self, instance: TkWidget, owner: object = None):
        return super().__get__(instance, owner) == self._truthy

    def __set__(self, instance: TkWidget, value: object):
        return super().__set__(instance, self._truthy if value else self._falsy)


class Font:
    """
    A mutable font object, that can be linked to a Tukaan widget.

    Attributes:
        info: If the font was loaded from a file, this object gives access
            to it's name information
        path: If the font was loaded from a file, stores the filepath
    """

    info: FontInfo | None = None
    path: Path | None = None

    def __init__(
        self,
        family: FontFile | str | None = None,
        size: int | None = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> None:
        """
        __init__

        Args:
            family:
                The font family to be used
            size:
                The font size to be used
            bold:
                Bold font ?
            italic:
                Italic font ?
            underline:
                Underlined font ?
            strikethrough:
                Throughstricken font ?
        """
        if isinstance(family, FontFile):
            if isinstance(family, TrueTypeCollection):
                raise FontError(
                    f"must specify font family for font collections. Available subfamilies: {[x.info.family for x in family.fonts]}"
                )
            else:
                family = family.info.family
        elif not family:
            family = "TkDefaultFont"

        if family in preset_fonts:
            self._name = family
        else:
            self._name = f"tukaan_font_{next(counts['fonts'])}"

        self.config(family, size, bold, italic, underline, strikethrough)
        _fonts[self._name] = self

    def __repr__(self) -> str:
        return f"Font(family={self.family!r}, size={self.size})"

    def config(
        self,
        family: str | None = None,
        size: int | None = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> None:
        """Configures the fonts parameters"""
        if isinstance(size, float):
            size = round(size)

        args = Tcl.to_tcl_args(
            family=family,
            size=size,
            weight="bold" if bold else "normal",
            slant="italic" if italic else "roman",
            underline=underline,
            overstrike=strikethrough,
        )

        try:
            Tcl.call(None, "font", "create", self._name, *args)
        except TclError:
            # Font already exists in Tcl
            Tcl.call(None, "font", "configure", self._name, *args)

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> Font | dict[str, str | int | bool]:
        try:
            return _fonts[tcl_value]
        except KeyError:
            types = {
                "family": str,
                "size": int,
                "bold": bool,
                "italic": bool,
                "underline": bool,
                "strikethrough": bool,
            }

            kwargs = {}
            flat_values = Tcl.get_iterable(tcl_value)
            for key, value in seq_pairs(flat_values):
                # TODO: Return a FontFile object if the family is loaded from a file
                key = key.lstrip("-")
                if key == "weight":
                    value = value == "bold"
                    key = "bold"
                elif key == "slant":
                    value = value == "italic"
                    key = "italic"
                elif key == "overstrike":
                    key = "strikethrough"
                kwargs[key] = Tcl.from_(types[key], value)

            return kwargs

    family = _StrFontProperty()
    """Get or set the current font family."""

    size = _IntFontProperty()
    """Get or set the current font size."""

    bold = _FontStyleProperty("weight", "bold", "normal")
    """Get or set whether the font should be drawn as bold."""

    italic = _FontStyleProperty("slant", "italic", "roman")
    """Get or set whether the font should be drawn as italic."""

    underline = _BoolFontProperty()
    """Get or set whether the font should have underlining."""

    strikethrough = _BoolFontProperty("overstrike")
    """Get or set whether the font should be striked through."""

    def dispose(self) -> None:
        """
        Delete the Python as well as the Tcl font object.

        The font won't be usable again, but the previous uses will be preserved.
        """
        Tcl.call(None, "font", "delete", self._name)
        del _fonts[self._name]

    def measure(self, text: str) -> int:
        """Measure, how wide the text would be with the current font family."""
        return Tcl.call(int, "font", "measure", self, text)

    @property
    def metrics(self) -> FontMetrics:
        """Compute the metrics of the current font family."""
        result = Tcl.call(
            {"-ascent": int, "-descent": int, "-linespace": int, "-fixed": bool},
            "font",
            "metrics",
            self,
        )
        return FontMetrics(*tuple(result.values()))


def font(
    family: FontFile | str | None = None,
    size: int | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strikethrough: bool | None = None,
) -> tuple[str, ...]:
    """
    This function doesn't create a font object, just converts the
    font description to a form understandable by Tcl.

    >>> t = tukaan.Label(..., font=tukaan.font(bold=True))
    """

    if isinstance(family, FontFile):
        if isinstance(family, TrueTypeCollection):
            raise FontError(
                f"must specify font family for font collections. Available subfamilies: {[x.info.family for x in family.fonts.values()]}"
            )
        else:
            family = family.info.family
    elif not family:
        family = "TkDefaultFont"

    weight = {None: None, True: "bold", False: "normal"}[bold]
    slant = {None: None, True: "italic", False: "roman"}[italic]

    return Tcl.to_tcl_args(
        family=family,
        size=size,
        weight=weight,
        slant=slant,
        underline=underline,
        overstrike=strikethrough,
    )
