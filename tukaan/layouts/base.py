from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tukaan._base import WidgetBase


class LayoutManagerBase(ABC):
    layout_managers = {}

    def __init_subclass__(cls, name: str | None = None) -> None:
        if not name:
            name = cls.__name__.lower()
        LayoutManagerBase.layout_managers[name] = cls

    def __init__(self, owner: WidgetBase) -> None:
        self._owner = owner

    @abstractmethod
    def __call__(self, *args, **kwargs) -> None:
        ...
