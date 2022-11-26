from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn

try:
    from PIL import Image as PillowImage
    from PIL import _imagingtk as ImagingTk  # type: ignore  # noqa: N812
except ImportError as e:
    raise ImportError("Tukaan needs PIL and PIL._imagingtk to work with images.") from e

from libtukaan import Serif

from tukaan._tcl import Tcl
from tukaan.theming import LookAndFeel, NativeTheme, Theme


class App:
    _exists = False
    shared_instance: App

    def __init__(
        self,
        name: str = "Tukaan",
        author: str = "unknown",
        version: int | str = "1.0",
        *,
        screen: str | None = None,
    ) -> None:
        if App._exists:
            raise Exception
        else:
            App._exists = True

        Tcl.init(name, screen)

        Serif.init()

        try:
            # TODO: remove this try block, when Pillow 9.3.0 becomes 4-5 months old,
            # and require Pillow>=9.3.0
            ImagingTk.tkinit(Tcl.interp_address, 1)
        except TypeError:
            # Pillow 9.3.0
            ImagingTk.tkinit(Tcl.interp_address)

        NativeTheme.use()

        self._name = name
        self._author = author
        self._version = str(version)

        App.shared_instance = self

        App.shared_instance = self

    def __enter__(self) -> App:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, _
    ) -> NoReturn | None:

        if exc_type is None:
            return self.run()

        raise exc_type(exc_value) from None

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
    def screen(self) -> str:
        # TODO: implement screen handling for window classes, not for App
        return Tcl.call(str, "winfo", "screen", ".")

    @property
    def theme(self) -> None:
        ...

    @theme.setter
    def theme(self, theme: Theme) -> None:
        theme.use()
        LookAndFeel._is_current_theme_native = theme.is_native

    @classmethod
    def quit(cls) -> None:
        """Quit the entire Tcl interpreter."""
        Serif.cleanup()
        Tcl.quit()

    @classmethod
    def run(cls) -> None:
        """Start the main event loop."""
        Tcl.main_loop()
