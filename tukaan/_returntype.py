from __future__ import annotations

from typing import Any

from ._utils import reversed_dict


class Callback:
    ...


class DictKey:
    def __init__(self, dict: dict[str, Any]):
        self.dictionary = dict

    def __getitem__(self, key: Any) -> Any:
        return reversed_dict(self.dictionary)[key]
