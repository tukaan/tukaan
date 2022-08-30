import sys
from pathlib import Path

from libtukaan import Serif

from ._base import WindowBase
from ._tcl import Tcl
from .exceptions import AppError


class App(WindowBase):
    _exists = False
    _name = _lm_path = ".app"
    _wm_path = "."

    def __init__(
        self,
        title: str = "Tukaan",
        *,
        width: int = 300,
        height: int = 200,
    ) -> None:
        if not App._exists:
            App._exists = True
        else:
            raise AppError("can't create multiple App instances. Use tukaan.Window instead.")

        super().__init__()

        Tcl.init()
        Tcl.eval(None, "pack [ttk::frame .app] -expand 1 -fill both")

        Tcl.call(None, "bind", self, "<Map>", self._generate_state_event)
        Tcl.call(None, "bind", self, "<Unmap>", self._generate_state_event)
        Tcl.call(None, "bind", self, "<Configure>", self._generate_state_event)
        Tcl.call(None, "wm", "protocol", self._wm_path, "WM_DELETE_WINDOW", self.destroy)

        self._set_title(title)
        self._set_size((width, height))

        self._init_tkdnd()
        Serif.init()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is None:
            return self.run()

        raise exc_type(exc_value) from None

    def _init_tkdnd(self):
        os = {"linux": "linux", "darwin": "mac", "win32": "win"}[sys.platform]
        os += "-x64" if sys.maxsize > 2**32 else "-x32"

        Tcl.call(None, "lappend", "auto_path", Path(__file__).parent / "tkdnd" / os)
        Tcl.call(None, "package", "require", "tkdnd")

    def destroy(self) -> None:
        """Quit the entire Tcl interpreter."""
        Serif.cleanup()

        Tcl.call(None, "destroy", self._name)
        Tcl.call(None, "destroy", self._wm_path)

        Tcl.quit_interp()

    def run(self) -> None:
        """Start the main event loop."""
        Tcl.main_loop()
