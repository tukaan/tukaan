from __future__ import annotations

from collections import namedtuple

Bbox = namedtuple("Bbox", ["x", "y", "width", "height"])
Position = namedtuple("Position", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])
OsVersion = namedtuple("OsVersion", ["major", "minor", "build"])
Version = namedtuple("Version", ["major", "minor", "patchlevel"])
