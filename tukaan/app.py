from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn

from libtukaan import Serif

from tukaan.theming import LookAndFeel, NativeTheme, Theme

from ._tcl import Tcl


class App:
    _exists = False

    def __init__(
        self,
        name: str = "Tukaan",
        author: str = "unknown",
        version: int | str = "1.0",
        *,
        x_screen: str | None = None,
    ) -> None:
        if App._exists:
            raise Exception
        else:
            App._exists = True

        Tcl.init(name, x_screen)

        Serif.init()
        self._init_tkdnd()

        self._name = name
        self._author = author
        self._version = str(version)

        NativeTheme.use()

    def _init_tkdnd(self) -> None:
        os = {"linux": "linux", "darwin": "mac", "win32": "win"}[sys.platform]
        os += "-x64" if sys.maxsize > 2**32 else "-x32"

        Tcl.call(None, "lappend", "auto_path", Path(__file__).parent / "tkdnd" / os)
        Tcl.call(None, "package", "require", "tkdnd")

    @property
    def name(self) -> str:
        return self._name

    @property
    def author(self) -> str:
        return self._author

    @property
    def version(self) -> str:
        return self._version

    @property
    def x_screen(self) -> str:
        return Tcl.call(str, "winfo", "screen", ".")

    @property
    def theme(self) -> None:
        ...

    @theme.setter
    def theme(self, theme: Theme) -> None:
        theme.use()
        LookAndFeel._is_current_theme_native = theme.is_native

    run = Tcl.main_loop
    async_event_loop = Tcl.async_main_loop

    @staticmethod
    def quit() -> None:
        """Quit the entire Tcl interpreter."""
        Serif.cleanup()
        Tcl.quit()
