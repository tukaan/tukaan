from __future__ import annotations

from collections import namedtuple
from pathlib import Path
from typing import Type

from ._utils import _fonts, _sequence_pairs, counts, get_tcl_interp, py_to_tcl_args
from .exceptions import FontError, TclError

font_props = {
    "compatible_full_name": "compatibleFullName",
    "copyright": "copyright",
    "dark_bg_palette": "darkBackgroundPalette",
    "description": "description",
    "designer": "designer",
    "designer_url": "designerURL",
    "family": "fontFamily",
    "subfamily": "fontSubfamily",
    "full_name": "fullName",
    "license": "license",
    "license_url": "licenseURL",
    "light_bg_palette": "lightBackgroundPalette",
    "manufacturer": "manufacturer",
    "manufacturer_url": "manufacturerURL",
    "post_script_find_font_name": "postScriptFindFontName",
    "post_script_name": "postScriptName",
    "preferred_family": "preferredFamily",
    "preferred_subfamily": "preferredSubfamily",
    "reserved": "reserved",
    "sample_text": "sampleText",
    "trademark": "trademark",
    "unique_ID": "uniqueID",
    "variations_post_script_name_prefix": "variationsPostScriptNamePrefix",
    "version": "version",
    "wss_family": "wwsFamily",
    "wss_subfamily": "wwsSubfamily",
}

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

FontMetrics = namedtuple("FontMetrics", ["ascent", "descent", "linespace", "fixed"])


class FontMetaData(namedtuple("FontMetadata", list(font_props.keys()))):
    def __new__(cls, owner: Font) -> FontMetaData:
        nameinfo_result = owner._interp._tcl_call("noconvert", "extrafont::nameinfo", owner.path)
        items = owner._interp._split_list(nameinfo_result[0])

        result = {}
        for key, value in _sequence_pairs(items):
            result[str(key)] = str(value)

        kwargs = {}
        for name, tcl_name in tuple(font_props.items()):
            kwargs[name] = result.get(tcl_name, None)

        return super(FontMetaData, cls).__new__(cls, **kwargs)

    def __init__(self, owner: Font) -> None:
        self.owner = owner

    def __getitem__(self, key: str) -> tuple:  # type: ignore[override]
        return getattr(self, key)

    def __repr__(self) -> str:
        return f"<FontMetadata object of {self.owner}>"

    __bool__ = lambda *_: True


class Font:
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

        self.path = file
        self.metadata = None

        self._interp = get_tcl_interp()

        if file is not None:
            if isinstance(file, Path):
                file = str(file.resolve())

            try:
                self._interp._tcl_call(None, "extrafont::load", self.path)
            except TclError as e:
                if str(e) == 'key "fontFamily" not known in dictionary':
                    raise FontError(f"missing or invalid metadata in file {self.path!r}") from None

            self.metadata = FontMetaData(self)

        if family in _preset_fonts:
            self._name = family
        else:
            self._name = f"tukaan_font_{next(counts['fonts'])}"

        if family is None and self.metadata:
            family = self.metadata.preferred_family
        elif family is None and self.path is None:
            family = "TkDefaultFont"

        self.config(family, size, bold, italic, underline, strikethrough)

        _fonts[self._name] = self

    def config(
        self,
        family: str = None,
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> None:
        args = py_to_tcl_args(
            family=family,
            size=size,
            weight="bold" if bold else "normal",
            slant="italic" if italic else "roman",
            underline=underline,
            overstrike=strikethrough,
        )

        try:
            self._interp._tcl_call(None, "font", "create", self._name, *args)
        except TclError:
            # font already exists in tcl
            self._interp._tcl_call(None, "font", "configure", self._name, *args)

    def to_tcl(self) -> str:
        return self._name

    @classmethod
    def from_tcl(cls, tcl_value: str) -> Font:
        return _fonts[tcl_value]

    def __getitem__(self, key: str) -> int | str | bool:
        return getattr(self, key)

    def _get(self, type_spec: Type[int] | Type[str] | Type[bool], option: str) -> int | str | bool:
        return self._interp._tcl_call(type_spec, "font", "actual", self, f"-{option}")

    def _set(self, option: str, value: int | str | bool) -> None:
        self._interp._tcl_call(None, "font", "configure", self._name, f"-{option}", value)

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
        return sorted(
            list(set(cls._interp._tcl_call([str], "font", "families")))
        )  # set to remove duplicates

    def measure(self, text: str) -> int:
        return get_tcl_interp()._tcl_call(int, "font", "measure", self, text)

    @property
    def metrics(self) -> FontMetrics:
        result = self._interp._tcl_call(
            {"-ascent": int, "-descent": int, "-linespace": int, "-fixed": bool},
            "font",
            "metrics",
            self,
        )
        return FontMetrics(*tuple(result.values()))

    def delete(self) -> None:
        get_tcl_interp()._tcl_call(None, "font", "delete", self._name)
        del _fonts[self._name]
