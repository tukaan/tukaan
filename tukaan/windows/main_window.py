from __future__ import annotations

from typing import Callable

from tukaan._base import ToplevelBase
from tukaan._tcl import Tcl
from tukaan.app import App
from tukaan.enums import WindowType
from tukaan.exceptions import AppError

from .wm import WindowManager


class MainWindow(ToplevelBase, WindowManager):
    _exists = False
    _name = _lm_path = ".app"
    _wm_path = "."

    def __init__(
        self,
        title: str = "Tukaan",
        *,
        width: int = 300,
        height: int = 200,
        type: WindowType | None = None,
        on_load: Callable = None,
    ) -> None:
        if MainWindow._exists:
            raise AppError("can't create multiple App instances. Use tukaan.Window instead.")
        else:
            MainWindow._exists = True

        ToplevelBase.__init__(self)

        Tcl.eval(None, "pack [ttk::frame .app] -expand 1 -fill both")
        Tcl.call(None, "wm", "title", ".", title)
        Tcl.call(None, "wm", "geometry", ".", f"{width}x{height}")
        Tcl.call(None, "wm", "protocol", ".", "WM_DELETE_WINDOW", self.destroy)

        Tcl.call(None, "bind", ".app", "<Map>", self._gen_state_event)
        Tcl.call(None, "bind", ".app", "<Unmap>", self._gen_state_event)
        Tcl.call(None, "bind", ".app", "<Configure>", self._gen_state_event)

        if type is not None:
            self.type = type

        if hasattr(self, "setup"):
            Tcl.call(None, "update", "idletasks")
            self.setup()

        Tcl.call(None, "wm", "deiconify", ".")

        if callable(on_load):
            on_load()

        Tcl.call(None, "update", "idletasks")

    def destroy(self) -> None:
        """Destroy all widgets and quit the interpreter."""
        Tcl.call(None, "destroy", self._name)
        Tcl.call(None, "destroy", self._wm_path)

        App.quit()
