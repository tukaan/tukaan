from __future__ import annotations

from typing import NoReturn

try:
    from PIL import _imagingtk as ImagingTk  # type: ignore  # noqa: N812
except ImportError as e:
    raise ImportError("Tukaan needs PIL and PIL._imagingtk to work with images.") from e

from libtukaan import Serif, Xcursor

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

        try:
            Tcl.init(name, screen)
        except Exception as e:
            raise e
        else:
            App._exists = True

        Serif.init()
        if Tcl.windowing_system == "x11":
            Xcursor.init()
        ImagingTk.tkinit(Tcl.interp_address)

        NativeTheme.use()

        self._name = name
        self._author = author
        self._version = str(version)

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
        """Destroy all widgets and quit the Tcl interpreter."""
        Serif.cleanup()
        Xcursor.cleanup_cursors()
        Tcl.call(None, "destroy", ".app")
        Tcl.call(None, "destroy", ".")
        App.shared_instance = None
        Tcl.quit()

    @classmethod
    def run(cls) -> None:
        """Start the main event loop."""
        Tcl.main_loop()
