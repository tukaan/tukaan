from __future__ import annotations

import collections
import collections.abc
import itertools
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

if TYPE_CHECKING:
    from PIL import Image  # type: ignore

    from ._base import TkWidget
    from ._images import Icon, Pillow2Tcl
    from ._variables import ControlVariable
    from .fonts import Font
    from .timeouts import Timeout


class count:
    """Simplified itertools.count"""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        yield self._count

    def __int__(self) -> int:
        return self._count


counts: DefaultDict[Any, Iterator[int]] = collections.defaultdict(lambda: count())


_commands: dict[str, Callable[..., Any]] = {}
_fonts: dict[str, Font] = {}
_images: dict[str, Icon | Pillow2Tcl] = {}
_pil_images: dict[str, Image.Image] = {}
_text_tags: dict[str, Any] = {}
_timeouts: dict[str, Timeout] = {}
_variables: dict[str, ControlVariable] = {}
_widgets: dict[str, TkWidget] = {}


flatten = itertools.chain.from_iterable


def reversed_dict(dictionary: dict) -> dict:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence):
    return zip(sequence[::2], sequence[1::2])
