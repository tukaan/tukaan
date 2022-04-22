from __future__ import annotations

import struct
from collections import namedtuple
from pathlib import Path
from typing import BinaryIO, Iterator

from tukaan._tcl import Tcl
from tukaan._utils import _fonts, counts, seq_pairs
from tukaan.exceptions import FontError, TclError

nameID_order = (
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
)

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


class FontNameInfo:
    """A class that parses the font file with the help of `struct.unpack`.

    This is a pure Python implementation, though I translated it from Tcl.
    """

    @classmethod
    def get_from_file(cls, file_path: Path) -> list[dict[str, str]]:
        """Gets info from the specified font file.

        Raises:
            FontError: If the magic-tag in the file header can't be recognized.
        """

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
                raise FontError(f"unrecognized magic-tag for OpenType font: 0x{magic_tag.hex()}")

        return fonts_info

    @staticmethod
    def read_ttc_header(file: BinaryIO) -> tuple[int, ...]:
        """Parses the header of a TrueType collection font
        in order to get the offsets of the contained subfamilies.

        Returns:
            A tuple with the offsets counted in bytes.

        """

        *_, num_fonts = struct.unpack(">HHI", file.read(8))
        return struct.unpack(f">{num_fonts}I", file.read(num_fonts * 4))

    @classmethod
    def read_simple_font_file(cls, file: BinaryIO) -> dict[str, str]:
        """Reads a simple font file, or a subfamily of a TTC font.

        Returns:
            The name info of the font family.
        """

        num_tables, *_ = struct.unpack(">4H", file.read(8))
        for _ in range(num_tables):
            table_name, _, start, _ = struct.unpack(">4sL2I", file.read(16))
            if table_name == b"name":  # We don't care about the other tables
                return cls.read_name_table(file, start)

    @staticmethod
    def read_name_table(file: BinaryIO, start: float) -> dict[str, str]:
        """Parses the name table of the font file.

        Returns:
             A dictionary with the field-value pairs.
        """

        file.seek(start)
        _, num_records, str_offset = struct.unpack(">HHH", file.read(6))

        records = []
        for _ in range(num_records):
            records.append(
                struct.unpack(">6H", file.read(12))  # Each record is made of 6 unsigned short
            )

        name_info = {}
        storage_start = start + str_offset

        for platformID, encID, _, nameID, length, offset in records:
            if nameID > 25:
                # Don't care about invalid records
                break

            file.seek(storage_start + offset)
            value, *_ = struct.unpack(f">{length}s", file.read(length))

            if (platformID, encID) == (1, 0):  # 1 == Macintosh
                encoding = "utf-8"
            elif (platformID, encID) == (3, 1):  # 3 == Windows
                encoding = "utf-16-be"  # Microsoft: All string data for platform 3 must be encoded in UTF-16BE.
            else:
                raise FontError(
                    f"unknown platform or encoding specification in font file: {file.name!r}"
                )

            name_info[nameID_order[nameID]] = value.decode(encoding)
            # If the value already exists, just update it with the newly decoded one

        {name_info.setdefault(key) for key in nameID_order}

        return name_info


class Serif:
    """Interface class between the Serif C extension and Python.

    Attributes:
        loaded_fonts: A dictionary that contains the path of the
            loaded files along with the font families contained in them.
    """

    loaded_fonts: dict[Path, list[str]] = {}

    @classmethod
    def load(cls, file_path: Path) -> list[str]:
        """Loads a font file specified by `file_path`.
        The file may contain multiple font families.
        If the font file is already loaded, does nothing.

        Returns:
            A list of the font family names contained in the file.
        """

        if file_path in cls.loaded_fonts:
            return cls.loaded_fonts[file_path]

        Tcl.call(None, "Serif::load_fontfile", file_path)

        info = FontNameInfo.get_from_file(file_path)
        families = []
        for family in info:
            family_name = family["family"]

            if family_name is None:
                raise FontError(f"invalid or missing info in font file: {file_path.resolve()!s}")

            families.append(family_name)

        cls.loaded_fonts[file_path] = family_name

        return families, info

    @classmethod
    def unload(cls, file_path: Path) -> None:
        """
        Unloads a previously loaded font file specified by `file_path`.
        If the file wasn't loaded, does nothing.
        """

        if file_path in cls.loaded_fonts:
            Tcl.call(None, "Serif::unload_fontfile", file_path)

    @classmethod
    def cleanup(cls) -> None:
        """Unloads all loaded fonts."""

        for font in cls.loaded_fonts:
            cls.unload(font)

    @classmethod
    def get_info(cls, file_path: Path) -> list[dict[str, str]]:
        """Gets info from the specified font file. If it was
        previously loaded with Serif.load, returns the cached info.
        """

        if file_path in cls.loaded_fonts:
            return cls.loaded_fonts[file_path]
        return FontNameInfo.get_from_file(file_path)


class FontInfo(namedtuple("FontInfo", nameID_order)):
    """Stores information about a font family"""

    def __iter__(self) -> Iterator[str, str]:
        """Makes it possible to convert the FontInfo to a dictionary.

        Yields:
            The field-value pairs.
        """

        for key in nameID_order:
            yield key, getattr(self, key)


FontMetrics = namedtuple("FontMetrics", ["ascent", "descent", "line_spacing", "fixed"])


class Font:
    """A mutable font object, that can be linked to a Tukaan widget.

    Attributes:
        info: If the font was loaded from a file, this object gives access
            to it's name information
        path: If the font was loaded from a file, stores the filepath
    """

    info: FontInfo | None = None
    path: Path | None = None

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
        """__init__

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
            file:
                A font file to load the family from.
        """
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

            self.info = FontInfo(**info[families.index(family)])
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
        """Configures the fonts parameters"""

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
        """Gets or sets the current font family."""
        return self._get(str, "family")

    @family.setter
    def family(self, value: str) -> None:
        self._set("family", value)

    @property
    def size(self) -> int:
        """Gets or sets the current font size."""
        return self._get(int, "size")

    @size.setter
    def size(self, value: int):
        self._set("size", value)

    @property
    def bold(self) -> bool:
        """Gets or sets whether the font should be drawn as bold."""
        return self._get(str, "weight") == "bold"

    @bold.setter
    def bold(self, value: bool) -> None:
        self._set("weight", "bold" if value else "normal")

    @property
    def italic(self) -> bool:
        """Gets or sets whether the font should be drawn as italic."""
        return self._get(str, "slant") == "italic"

    @italic.setter
    def italic(self, value: bool) -> None:
        self._set("slant", "italic" if value else "roman")

    @property
    def underline(self) -> bool:
        """Gets or sets whether the font should have underlining."""
        return self._get(bool, "underline")

    @underline.setter
    def underline(self, value: bool) -> None:
        self._set("underline", value)

    @property
    def strikethrough(self) -> bool:
        """Gets or sets whether the font should be striked through."""
        return self._get(bool, "overstrike")

    @strikethrough.setter
    def strikethrough(self, value: bool) -> None:
        self._set("overstrike", value)

    def delete(self) -> None:
        """Deletes the Python as well as the Tcl font object.
        The font won't be usable again, but the previous uses will be preserved.
        """
        Tcl.call(None, "font", "delete", self._name)
        del _fonts[self._name]

    def measure(self, text: str, /) -> int:
        """Measures, how wide the text would be with the current font family."""
        return Tcl.call(int, "font", "measure", self, text)

    @property
    def metrics(self) -> FontMetrics:
        """Computes the metrics of the current font family."""

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
    """This function doesn't create a font object, just converts the
    font description to a form understandable by Tcl.

    >>> t = tukaan.TextBox(app, font=tukaan.font(bold=True))
    """

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
