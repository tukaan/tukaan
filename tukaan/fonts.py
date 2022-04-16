from __future__ import annotations

import struct
from collections import namedtuple
from pathlib import Path
from typing import BinaryIO

from tukaan._tcl import Tcl
from tukaan._utils import _fonts, counts, seq_pairs
from tukaan.exceptions import FontError, TclError

nameID_order = [
    "copyright",
    "family",
    "subfamily",
    "unique_ID",
    "full_name",
    "version",
    "post_script_name",
    "trademark",
    "manufacturer",
    "designer",
    "description",
    "manufacturer_URL",
    "designer_URL",
    "license",
    "license_URL",
    "reserved",
    "preferred_family",
    "preferred_subfamily",
    "compatible_full_name",
    "sample_text",
    "post_script_find_font_name",
    "WWS_family",
    "WWS_subfamily",
    "light_bg_palette",
    "dark_bg_palette",
    "variations_post_script_name_prefix",
]

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


class FontInfo:
    @classmethod
    def get_from_file(cls, file_path: Path) -> list[dict[str, str]]:
        fonts_info = []

        with file_path.open("rb") as file:
            magic_tag = file.read(4)  # First 4 byte is the magic tag

            if magic_tag == b"ttcf":
                for offset in cls.read_ttc_header(file):
                    file.seek(offset + 4)  # +4 to skip subfamily magic tag
                    fonts_info.append(cls.read_simple_font_file(file))
            elif magic_tag in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"}:
                fonts_info.append(cls.read_simple_font_file(file))
            else:
                raise FontError(f"unrecognized magic-number for OpenType font: 0x{magic_tag.hex()}")

        return fonts_info

    @staticmethod
    def read_ttc_header(file: BinaryIO) -> tuple[int, ...]:
        *_, num_fonts = struct.unpack(">HHI", file.read(8))
        return struct.unpack(f">{num_fonts}I", file.read(num_fonts * 4))

    @classmethod
    def read_simple_font_file(cls, file: BinaryIO) -> dict[str, str]:
        num_tables, *_ = struct.unpack(">4H", file.read(8))
        for _ in range(num_tables):
            table_name, _, start, _ = struct.unpack(">4sL2I", file.read(16))
            if table_name == b"name":  # We don't care about the other tables
                return cls.read_name_table(file, start)

    @staticmethod
    def read_name_table(file: BinaryIO, start: float) -> dict[str, str]:
        file.seek(start)
        _, num_records, str_offset = struct.unpack(">HHH", file.read(6))

        records = []
        for _ in range(num_records):
            records.append(
                struct.unpack(">6H", file.read(12))
            )  # Each record is made of 6 unsigned short

        name_info = {}
        storage_start = start + str_offset
        base_tripplet = struct.pack(">hhh", 1, 0, 0)
        for platformID, encodingID, languageID, nameID, length, offset in records:
            if nameID > 25:
                break

            if base_tripplet == struct.pack(">hhh", platformID, encodingID, languageID):
                file.seek(storage_start + offset)
                value, *_ = struct.unpack(f">{length}s", file.read(length))
                name_info[nameID_order[nameID]] = value.decode("latin-1")

        for key in nameID_order:
            if key not in name_info:
                name_info[key] = None

        return name_info


class Serif:
    loaded_fonts = {}

    @classmethod
    def load(cls, file_path: Path) -> list[str]:
        if file_path in cls.loaded_fonts:
            return cls.loaded_fonts[file_path]

        Tcl.call(None, "Serif::load_fontfile", file_path)

        info = FontInfo.get_from_file(file_path)
        families = []
        for family in info:
            family_name = family["family"]

            if family_name is None:
                raise FontError(
                    f"invalid or missing metadata in font file: {file_path.resolve()!s}"
                )

            families.append(family_name)

        cls.loaded_fonts[file_path] = family_name

        return families, info

    @staticmethod
    def unload(file_path: Path) -> None:
        Tcl.call(None, "Serif::unload_fontfile", file_path)

    @classmethod
    def cleanup(cls):
        for font in cls.loaded_fonts:
            cls.unload(font)

    @classmethod
    def get_metadata(cls, file_path: Path):
        if file_path in cls.loaded_fonts:
            return cls.loaded_fonts[file_path]
        return FontInfo.get_from_file(file_path)


class FontMetadata(namedtuple("FontMetadata", nameID_order)):
    def __iter__(self):
        for key in nameID_order:
            yield key, getattr(self, key)


FontMetrics = namedtuple("FontMetrics", ["ascent", "descent", "line_spacing", "fixed"])


class Font:
    path: Path | None = None
    metadata: FontMetadata | None = None

    def __init__(
        self,
        family: str | None = None,
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        *,
        file: Path | None = None,
    ) -> None:
        if isinstance(family, Path):
            file = family

        if file:
            if not isinstance(file, Path):
                self.path = Path(file)
            else:
                self.path = file

            families, info = Serif.load(self.path)

            if not family:
                if len(families) == 1:
                    family = families[0]
                else:
                    raise FontError(
                        f"must specify font family for font collections. Available subfamilies: {families}"
                    )
            elif family not in families:
                raise FontError(f"the family {family} can't be found in this font file")

            self.metadata = FontMetadata(**info[families.index(family)])
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
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
    ) -> None:
        args = Tcl.to_tcl_args(
            family=family,
            size=round(size),
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
    def __from_tcl__(cls, tcl_value: str) -> Font:
        try:
            return _fonts[tcl_value]
        except KeyError:
            flat_values = Tcl.get_iterable(tcl_value)
            types = {
                "family": str,
                "size": int,
                "bold": bool,
                "italic": bool,
                "underline": bool,
                "strikethrough": bool,
            }
            
            kwargs = {}
            for key, value in seq_pairs(flat_values):
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

            return cls(**kwargs)

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

    def delete(self) -> None:
        Tcl.call(None, "font", "delete", self._name)
        del _fonts[self._name]

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


def font(
    family: str | None = None,
    size: int | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strikethrough: bool | None = None,
) -> tuple[str, ...]:
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
