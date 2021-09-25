from __future__ import annotations

import platform

import _tkinter as tk

from ._utils import ClassPropertyMetaClass, classproperty, get_tcl_interp


class Platform(metaclass=ClassPropertyMetaClass):
    version: str = platform.version()
    node: str = platform.node()
    processor: str = platform.processor()
    machine: str = platform.machine()
    release: str = platform.release()
    system: str = platform.system()
    arch: tuple[str, str] = platform.architecture()

    @classproperty
    def windowing_system(cls) -> str:
        return get_tcl_interp()._tcl_call(str, "tk", "windowingsystem")

    @classproperty
    def tcl_version(cls) -> str:
        return get_tcl_interp()._tcl_call(str, "info", "patchlevel")

    @classproperty
    def tk_version(cls) -> float:
        return float(tk.TK_VERSION)
