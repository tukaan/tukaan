from __future__ import annotations

import collections
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

from tukaan._utils import count

if TYPE_CHECKING:
    from tukaan._base import TkWidget
    from tukaan._images import Icon, Pillow2Tcl
    from tukaan._variables import ControlVariable
    from tukaan.fonts.font import Font

counter: DefaultDict[Any, Iterator[int]] = collections.defaultdict(count)

_commands: dict[str, Callable[..., Any]] = {}
_fonts: dict[str, Font] = {}
_images: dict[str, Icon | Pillow2Tcl] = {}
_variables: dict[str, ControlVariable] = {}
_widgets: dict[str, TkWidget] = {}
