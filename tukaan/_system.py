from __future__ import annotations

import functools
import sys
from dataclasses import dataclass
from platform import python_version_tuple

from tukaan._typing import P, T, WrappedFunction


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patchlevel: int | None = None

    @classmethod
    def __from_tcl__(cls, value: str) -> Version:
        return Version(*(int(x) for x in value.split(".")))


class Platform:
    tcl_version: Version | None = None
    tk_version: Version | None = None
    dll_ext: str | None = None
    window_sys: str | None = None

    try:
        os = {"linux": "Linux", "darwin": "macOS", "win32": "Windows"}[sys.platform]
    except KeyError:
        os = sys.platform

    py_version = Version(*(int(i) for i in python_version_tuple()))

    def run_conditionally(condition: bool, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            if condition:
                return func(*args, **kwargs)
            else:
                return None

        return wrapper

    windows_only = staticmethod(functools.partial(run_conditionally, sys.platform == "win32"))
    macOS_only = staticmethod(functools.partial(run_conditionally, sys.platform == "darwin"))
    linux_only = staticmethod(functools.partial(run_conditionally, sys.platform == "linux"))
