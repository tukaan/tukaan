import functools
import platform
import sys
from typing import Any, NamedTuple

import _tkinter as tk

from tukaan._typing import P, T, WrappedFunction
from tukaan._utils import classproperty


class Version(NamedTuple):
    major: int
    minor: int
    patchlevel: int | None


class Platform:
    try:
        os = {"linux": "Linux", "win32": "Windows", "darwin": "macOS"}[sys.platform]
    except KeyError:
        os = sys.platform

    py_version = Version(*(int(item) for item in platform.python_version_tuple()))
    tk_major, tk_minor = tk.TK_VERSION.split(".")[:2]
    tk_version = Version(int(tk_major), int(tk_minor), None)

    @classproperty
    def tcl_version(self) -> Version:
        from tukaan._tcl import Tcl

        assert Tcl.version is not None
        return Version(*map(int, Tcl.version.split(".")))

    @classproperty
    def win_sys(self) -> str:
        from tukaan._tcl import Tcl

        assert Tcl.windowing_system is not None
        return Tcl.windowing_system

    @classmethod
    def windows_only(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T | None:
            if sys.platform == "win32":
                return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def mac_only(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T | None:
            if sys.platform == "darwin":
                return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def linux_only(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T | None:
            if sys.platform == "linux":
                return func(self, *args, **kwargs)

        return wrapper
