from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tukaan._base import TkWidget


class LayoutManagerBase(ABC):
    layout_managers: dict[str, type[LayoutManagerBase]] = {}

    def __init_subclass__(cls, name: str | None = None) -> None:
        if not name:
            name = cls.__name__.lower()
        LayoutManagerBase.layout_managers[name] = cls

    def __init__(self, owner_name: str, owner_toplevel_name: str) -> None:
        self._owner_name = owner_name
        self._owner_toplevel_name = owner_toplevel_name

    @abstractmethod
    def __call__(self, *args, **kwargs) -> None:
        ...
