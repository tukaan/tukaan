from __future__ import annotations

from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

from libtukaan import Serif

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
        size: int = None,
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
        size: int = None,
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

    def _get(self, type_spec: type[int] | type[str] | type[bool], option: str) -> int | str | bool:
        return Tcl.call(type_spec, "font", "actual", self, f"-{option}")

    def _set(self, option: str, value: int | str | bool) -> None:
        Tcl.call(None, "font", "configure", self._name, f"-{option}", value)

    @property
    def family(self) -> str:
        """Get or set the current font family."""
        return self._get(str, "family")

    @family.setter
    def family(self, value: str) -> None:
        self._set("family", value)

    @property
    def size(self) -> int:
        """Get or set the current font size."""
        return self._get(int, "size")

    @size.setter
    def size(self, value: int):
        self._set("size", value)

    @property
    def bold(self) -> bool:
        """Get or set whether the font should be drawn as bold."""
        return self._get(str, "weight") == "bold"

    @bold.setter
    def bold(self, value: bool) -> None:
        self._set("weight", "bold" if value else "normal")

    @property
    def italic(self) -> bool:
        """Get or set whether the font should be drawn as italic."""
        return self._get(str, "slant") == "italic"

    @italic.setter
    def italic(self, value: bool) -> None:
        self._set("slant", "italic" if value else "roman")

    @property
    def underline(self) -> bool:
        """Get or set whether the font should have underlining."""
        return self._get(bool, "underline")

    @underline.setter
    def underline(self, value: bool) -> None:
        self._set("underline", value)

    @property
    def strikethrough(self) -> bool:
        """Get or set whether the font should be striked through."""
        return self._get(bool, "overstrike")

    @strikethrough.setter
    def strikethrough(self, value: bool) -> None:
        self._set("overstrike", value)

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
