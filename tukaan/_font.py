from __future__ import annotations

from collections import namedtuple
from pathlib import Path
from typing import Type

from ._utils import _fonts, _sequence_pairs, counts, get_tcl_interp, py_to_tcl_args
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
        items = owner._interp._tcl_call([str], "Serif::getFontMetadata", owner.path)

        result = {}
        for key, value in _sequence_pairs(items):
            result[str(key)] = str(value)

        for property_ in font_props:
            if property_ not in result:
                result[property_] = None

        return super(FontMetadata, cls).__new__(cls, **result)

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

        if file and not isinstance(file, Path):
            self.path = Path(file)
        else:
            self.path = file
                
        self.metadata = None
        file_family = None

        self._interp = get_tcl_interp()

        if self.path:
            try:
                file_family = self._interp._tcl_call(str, "Serif::load", self.path)
            except TclError as e:
                if 'not known in dictionary' in str(e):
                    raise FontError(f"missing or invalid metadata in file {self.path!r}") from None
                raise e

            self.metadata = FontMetadata(self)

        if not family and file_family:
            family = file_family
        elif not family and not self.path:
            family = "TkDefaultFont"

        if family in _preset_fonts:
            self._name = family
        else:
            self._name = f"tukaan_font_{next(counts['fonts'])}"

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
            list(set(cls._interp._tcl_call([str], "font", "families")))  # set() to remove duplicates
        )

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
