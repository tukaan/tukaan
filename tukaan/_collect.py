from __future__ import annotations

from collections import defaultdict
from itertools import count
from typing import Any


class Collector:
    def __init__(self):
        self._counter = defaultdict(count)

    def add(self, category: str, obj: object, name: str | None = None) -> str:
        if not hasattr(self, category):
            setattr(self, category, {})

        container = getattr(self, category)

        if not name:
            name = f"tukaan_{category}_{next(self._counter[category])}"
        elif name in container:
            raise KeyError(f"object with name {name} already exsist in this container")

        container[name] = obj
        return name

    def remove_by_key(self, category: str, key: str) -> None:
        if not hasattr(self, category):
            return

        getattr(self, category).pop(key, None)

    def remove_by_object(self, category: str, obj: object) -> None:
        if not hasattr(self, category):
            return

        container = getattr(self, category)
        for k, v in container.items():
            if v is obj:
                del container[k]
                return

    def get_by_key(self, category: str, key: str) -> Any:
        if not hasattr(self, category):
            return None

        return getattr(self, category).get(key, None)

    def get_by_object(self, category: str, obj: object) -> str | None:
        if not hasattr(self, category):
            return None

        for k, v in getattr(self, category).items():
            if v is obj:
                return k
        return None


collector = Collector()
