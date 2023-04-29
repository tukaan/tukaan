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

commands: dict[str, Callable[..., Any]] = {}
fonts: dict[str, Font] = {}
images: dict[str, Icon | Pillow2Tcl] = {}
variables: dict[str, ControlVariable[Any]] = {}
widgets: dict[str, TkWidget] = {}
