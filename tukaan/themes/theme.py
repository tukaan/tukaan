from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from tukaan._info import System


class Theme(ABC):
    @abstractmethod
    def _set_theme(self):
        pass


class Win32Theme(Theme):
    def __init__(self):
        ...

    def _set_theme(self):
        ...


class AquaTheme(Theme):
    def __init__(self):
        ...

    def _set_theme(self):
        ...


class GtkTheme(Theme):
    def __init__(self, theme: Optional[str] = None):
        ...

    def _set_theme(self):
        ...


def native_theme():
    os = System.os

    if os == "Windows":
        return Win32Theme()
    elif os == "macOS":
        return AquaTheme()
    elif os == "Linux":
        return GtkTheme()
