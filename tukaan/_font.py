from __future__ import annotations

from collections import namedtuple
from pathlib import Path
from typing import Type

from ._tcl import Tcl
from ._utils import _fonts, counts, seq_pairs
from .exceptions import FontError, TclError

font_props = [
    "compatible_full_name",
    "copyright",
    "dark_bg_palette",
    "description",
    "designer",
    "designer_URL",
    "family",
    "full_name",
    "license",
    "license_URL",
    "light_bg_palette",
    "manufacturer",
    "manufacturer_URL",
    "post_script_find_font_name",
    "post_script_name",
    "preferred_family",
    "preferred_subfamily",
    "reserved",
    "sample_text",
    "subfamily",
    "trademark",
    "unique_ID",
    "variations_post_script_name_prefix",
    "version",
    "wws_family",
    "wws_subfamily",
]

_preset_fonts = {
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


FontMetrics = namedtuple("FontMetrics", ["ascent", "descent", "linespace", "monospace"])


class FontMetadata(namedtuple("FontMetadata", font_props)):
    def __new__(cls, owner: Font) -> FontMetadata:
        items = Tcl.call([str], "Serif::getFontMetadata", owner.path)

        result = {}
        for key, value in seq_pairs(items):
            result[str(key)] = str(value)

        for property_ in font_props:
            if property_ not in result:
                result[property_] = None

        return super().__new__(cls, **result)

    def __init__(self, owner: Font) -> None:
        self.owner = owner

    def __repr__(self) -> str:
        return f"<FontMetadata object of {self.owner}>"

    def __len__(self):
        return len(font_props)

    def __iter__(self):
        for key in font_props:
            yield key, getattr(self, key)

    __bool__ = lambda *_: True


class Font:
    path: None | Path
    metadata: None | FontMetadata

    def __init__(
        self,
        family: str = None,
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        *,
        file: str = None,
    ) -> None:

        self.path = None
        self.metadata = None

        if file:
            if not isinstance(file, Path):
                self.path = Path(file)
            else:
                self.path = file

            file_family = self.__load_font_file(self.path)
            if not family:
                family = file_family

            self.metadata = FontMetadata(self)
        elif not family:
            family = "TkDefaultFont"

        if family not in _preset_fonts:
            self._name = f"tukaan_font_{next(counts['fonts'])}"
        else:
            self._name = family

        self.config(family, size, bold, italic, underline, strikethrough)

        _fonts[self._name] = self

    def __repr__(self) -> str:
        return f"Font(family={self.family!r}, size={self.size})"

    def _load_font_file(self, path: Path) -> str:
        try:
            return Tcl.call(str, "Serif::load", self.path)
        except TclError as e:
            if "not known in dictionary" in str(e):
                raise FontError(f"missing or invalid metadata in file {self.path!r}") from None
            raise e

    def config(
        self,
        family: str = None,
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> None:
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
            # font already exists
            Tcl.call(None, "font", "configure", self._name, *args)

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, tcl_value: str) -> Font:
        return _fonts[tcl_value]

    def _get(self, type_spec: type[int] | type[str] | type[bool], option: str) -> int | str | bool:
        return Tcl.call(type_spec, "font", "actual", self, f"-{option}")

    def _set(self, option: str, value: int | str | bool) -> None:
        Tcl.call(None, "font", "configure", self._name, f"-{option}", value)

    @property
    def family(self) -> str:
        return self._get(str, "family")

    @family.setter
    def family(self, value: str) -> None:
        self._set("family", value)

    @property
    def size(self) -> int:
        return self._get(int, "size")

    @size.setter
    def size(self, value: int):
        self._set("size", value)

    @property
    def bold(self) -> bool:
        return self._get(str, "weight") == "bold"

    @bold.setter
    def bold(self, value: bool) -> None:
        self._set("weight", "bold" if value else "normal")

    @property
    def italic(self) -> bool:
        return self._get(str, "slant") == "italic"

    @italic.setter
    def italic(self, value: bool) -> None:
        self._set("slant", "italic" if value else "roman")

    @property
    def underline(self) -> bool:
        return self._get(bool, "underline")

    @underline.setter
    def underline(self, value: bool) -> None:
        self._set("underline", value)

    @property
    def strikethrough(self) -> bool:
        return self._get(bool, "overstrike")

    @strikethrough.setter
    def strikethrough(self, value: bool) -> None:
        self._set("overstrike", value)

    @property
    def families(cls):
        return sorted(list(set(Tcl.call([str], "font", "families"))))  # set to remove duplicates

    def measure(self, text: str) -> int:
        return Tcl.call(int, "font", "measure", self, text)

    @property
    def metrics(self) -> FontMetrics:
        result = Tcl.call(
            {"-ascent": int, "-descent": int, "-linespace": int, "-fixed": bool},
            "font",
            "metrics",
            self,
        )
        return FontMetrics(*tuple(result.values()))

    def delete(self) -> None:
        Tcl.call(None, "font", "delete", self._name)
        del _fonts[self._name]
