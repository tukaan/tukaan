import functools
import platform
import sys
from collections import namedtuple
from typing import Any, Callable

import _tkinter as tk

from ._utils import classproperty

Version = namedtuple("Version", ["major", "minor", "patchlevel"])


class Platform:
    try:
        os = {"linux": "Linux", "win32": "Windows", "darwin": "macOS"}[sys.platform]
    except KeyError:
        os = sys.platform

    py_version = Version(*map(int, platform.python_version_tuple()))
    tk_version = Version(*map(int, tk.TK_VERSION.split(".")[:2]), None)

    @classproperty
    def tcl_version(self) -> Version:
        from ._tcl import Tcl

        assert Tcl.version is not None
        return Version(*map(int, Tcl.version.split(".")))

    @classproperty
    def win_sys(self) -> str:
        from ._tcl import Tcl

        assert Tcl.windowing_system is not None
        return Tcl.windowing_system

    @classmethod
    def windows_only(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            if sys.platform == "win32":
                return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def mac_only(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            if sys.platform == "darwin":
                return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def linux_only(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            if sys.platform == "linux":
                return func(self, *args, **kwargs)

        return wrapper
