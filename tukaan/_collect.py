from __future__ import annotations

import collections
from typing import TYPE_CHECKING, Any, DefaultDict, Iterator

from tukaan._utils import count

if TYPE_CHECKING:
    from PIL import Image  # type: ignore

    from tukaan._images import Icon, Pillow2Tcl
    from tukaan._variables import ControlVariable

counter: DefaultDict[Any, Iterator[int]] = collections.defaultdict(count)

_images: dict[str, Icon | Pillow2Tcl] = {}
_pil_images: dict[str, Image.Image] = {}
_variables: dict[str, ControlVariable] = {}
