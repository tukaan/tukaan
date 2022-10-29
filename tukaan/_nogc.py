from __future__ import annotations

import collections
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

if TYPE_CHECKING:
    from PIL import Image  # type: ignore

    from ._base import TkWidget
    from ._images import Icon, Pillow2Tcl
    from ._variables import ControlVariable
    from .fonts import Font
    from .timeouts import Timeout


class count:
    """Simplified itertools.count, that can be int()-ed."""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        yield self._count

    def __int__(self) -> int:
        return self._count


counter: DefaultDict[Any, Iterator[int]] = collections.defaultdict(count)

_commands: dict[str, Callable[..., Any]] = {}
_fonts: dict[str, Font] = {}
_images: dict[str, Icon | Pillow2Tcl] = {}
_pil_images: dict[str, Image.Image] = {}
_text_tags: dict[str, Any] = {}
_timeouts: dict[str, Timeout] = {}
_variables: dict[str, ControlVariable] = {}
_widgets: dict[str, TkWidget] = {}
