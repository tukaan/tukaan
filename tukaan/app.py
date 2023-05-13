from __future__ import annotations

from tukaan._tcl import Tcl
from .errors import AppAlreadyExistsError


class App:
    _exists = False
    shared_instance: App

    def __init__(
        self,
        name: str = "Tukaan",
        author: str = "unknown",
        version: int | str = "1.0",
        *,
        display: str | None = None,
    ) -> None:
        if App._exists:
            raise AppAlreadyExistsError

        Tcl.initialize(name, display)
        App._exists = True
        App.shared_instance = self

        self._name = name
        self._author = author
        self._version = str(version)

    @classmethod
    def quit(cls) -> None:
        """Destroy all widgets and quit the Tcl interpreter."""
        Tcl.call(None, "destroy", ".app")
        Tcl.call(None, "destroy", ".")
        Tcl.quit()

    @classmethod
    def run(cls) -> None:
        """Start the main event loop."""
        Tcl.main_loop()

    @property
    def name(self) -> str:
        return self._name

    @property
    def author(self) -> str:
        return self._author

    @property
    def version(self) -> str:
        return self._version
