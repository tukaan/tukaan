from __future__ import annotations

import struct
from collections import namedtuple
from pathlib import Path
from typing import BinaryIO

from libtukaan import Serif

from tukaan.exceptions import FontError

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


class FontInfo(namedtuple("FontInfo", nameID_order)):
    """Store information about a font family."""

    def __iter__(self) -> Iterator[str, str]:
        """
        Make it possible to convert the FontInfo to a dictionary.

        Yields:
            The field-value pairs.
        """

        for key in nameID_order:
            yield key, getattr(self, key)


def get_font_type(magic_tag: bytes) -> str:
    """
    Determine the type of a font file based on the magic tag in the file header.

    Raises:
        FontError: If the magic tag in the file header can't be recognized.
    """

    if magic_tag == b"ttcf":
        return "ttc"
    elif magic_tag in {b"\x00\x01\x00\x00", b"true"}:
        return "ttf"
    elif magic_tag == b"OTTO":
        return "otf"
    else:
        raise FontError(f"unrecognized magic tag in font file: 0x{magic_tag.hex()}")


class FontFile:
    def __new__(cls, path: Path, **kwargs) -> FontFile:
        if path is not None and not isinstance(path, Path):
            raise TypeError("'path' should a pathlib.Path object")

        if cls is not FontFile:
            return super().__new__(cls)

        font_types = {"ttc": TrueTypeCollection, "ttf": TrueTypeFont, "otf": OpenTypeFont}
        return super().__new__(font_types[get_font_type(path.read_bytes()[:4])])

    def _parse(self, file: BinaryIO) -> FontInfo:
        num_tables, *_ = struct.unpack(">4H", file.read(8))
        for _ in range(num_tables):
            table_name, _, start, _ = struct.unpack(">4sL2I", file.read(16))
            if table_name == b"name":  # We don't care about the other tables
                return FontInfo(**self._read_name_table(file, start))

    def _read_name_table(self, file: BinaryIO, start: int) -> dict[str, str]:
        file.seek(start)
        _, num_records, str_offset = struct.unpack(">HHH", file.read(6))

        records = [struct.unpack(">6H", file.read(12)) for _ in range(num_records)]
        name_info = {}
        storage_start = start + str_offset

        for platformID, encID, _, nameID, length, offset in records:
            if nameID > 25:
                # Don't care about invalid records
                break

            file.seek(storage_start + offset)
            value, *_ = struct.unpack(f">{length}s", file.read(length))

            if (platformID, encID) == (1, 0):  # 1 == Macintosh
                encoding = "latin1"
            elif (platformID, encID) == (3, 1):  # 3 == Windows
                # Microsoft docs says: All string data for platform 3 must be encoded in UTF-16BE.
                encoding = "utf-16-be"
            else:
                # idk, should be error actually
                encoding = "latin1"

            # If the value already exists, just update it with the new one
            name_info[nameID_order[nameID]] = value.decode(encoding)

        {name_info.setdefault(key) for key in nameID_order}

        if name_info["family"] is None:
            raise FontError("couldn't load font file due to missing metadata")

        return name_info

    def dispose(self) -> None:
        Serif.unload(self.path)


class TrueTypeCollection(FontFile):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fonts = {}

        with path.open("rb") as file:
            for offset in self._read_header(file):
                file.seek(offset + 4)
                font = TrueTypeFont(None, _io=file)
                self.fonts[font.info.family] = font

    def _read_header(self, file: BinaryIO) -> tuple[int, ...]:
        file.seek(4)
        *_, num_fonts = struct.unpack(">HHI", file.read(8))
        return struct.unpack(f">{num_fonts}I", file.read(num_fonts * 4))

    def __getitem__(self, key: str) -> TrueTypeFont:
        return self.fonts[key]


class TrueTypeFont(FontFile):
    def __init__(self, path: Path | None, _io: BinaryIO | None = None) -> None:
        if _io is None:
            self.path = path
            file = path.open("rb")
            file.seek(4)
        else:
            self.path = Path(_io.name)
            file = _io

        self.info = self._parse(file)

        if _io is None:
            file.close()

        Serif.load(self.path)


class OpenTypeFont(FontFile):
    def __init__(self, path: Path | None) -> None:
        self.path = path

        with path.open("rb") as file:
            file.seek(4)
            self.info = self._parse(file)

        Serif.load(self.path)
