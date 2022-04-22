from __future__ import annotations

import collections
import collections.abc
import itertools
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

from ._info import System

if TYPE_CHECKING:
    from PIL import Image  # type: ignore

    from ._base import TkWidget
    from ._images import Icon, PIL_TclConverter
    from ._variables import _TclVariable
    from .audio import Sound
    from .fonts import Font
    from .textbox import Tag
    from .timeouts import Timeout


class count:
    """Simplified itertools.count"""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        # method to make mypy happy
        yield self._count

    def __int__(self) -> int:
        return self._count


counts: DefaultDict[Any, Iterator[int]] = collections.defaultdict(lambda: count())


_commands: dict[str, Callable] = {}
_images: dict[str, PIL_TclConverter | Icon] = {}
_pil_images: dict[str, Image] = {}
_timeouts: dict[str, Timeout] = {}
_variables: dict[str, _TclVariable] = {}
_text_tags: dict[str, Tag] = {}
_widgets: dict[str, TkWidget] = {}
_fonts: dict[str, Font] = {}
_sounds: dict[str, Sound] = {}


def windows_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "Windows":
            return func(*args, **kwargs)

    return wrapper


def mac_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "macOS":
            return func(*args, **kwargs)

    return wrapper


def linux_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "Linux":
            return func(*args, **kwargs)

    return wrapper


flatten = itertools.chain.from_iterable


def reversed_dict(dictionary: dict, /) -> dict:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence, /):
    return zip(sequence[0::2], sequence[1::2])
