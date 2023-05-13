from __future__ import annotations

from tukaan._tcl import Procedure, Tcl
from tukaan.app import App
from tukaan.errors import AppDoesNotExistError, MainWindowAlreadyExistsError


class MainWindow:
    _exists = False
    _toplevel_name = "."

    def __init__(self, title: str = "Tukaan", *, width: int = 300, height: int = 200) -> None:
        if not App._exists:
            raise AppDoesNotExistError(
                "too early to create main window. App context isn't initialized."
            )

        if MainWindow._exists:
            raise MainWindowAlreadyExistsError(
                "can't create multiple main windows. Use `tukaan.Window` instead."
            )
        else:
            MainWindow._exists = True

        Tcl.eval(None, "pack [ttk::frame .app] -expand 1 -fill both")
        Tcl.call(None, "wm", "title", ".", title)
        Tcl.eval(None, f"wm geometry . {width}x{height}")
        Tcl.call(None, "wm", "protocol", ".", "WM_DELETE_WINDOW", App.quit)

        Tcl.eval(None, "wm deiconify .")
        Tcl.eval(None, "update idletasks")

    def destroy(self) -> None:
        App.quit()
