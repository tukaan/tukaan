from __future__ import annotations

from tukaan._base import ToplevelBase, generate_pathname
from tukaan._collect import _widgets
from tukaan._tcl import Tcl
from tukaan.app import App
from tukaan.enums import WindowType

from .wm import WindowManager


class Window(ToplevelBase, WindowManager):
    _tcl_class = "toplevel"
    _keys = {}
    parent: App | Window

    def __init__(
        self,
        parent: App | Window,
        title: str = "Tukaan",
        *,
        width: int = 300,
        height: int = 200,
        x_type: WindowType | None = None,
    ) -> None:
        assert isinstance(parent, (App, ToplevelBase)), "Window parent must be an App or a Window"

        self._wm_path = generate_pathname(self, parent)
        self._name = self._lm_path = f"{self._wm_path}.frame"
        self.parent = parent
        self.parent._children[self._name] = self

        super().__init__()

        Tcl.call(None, self._tcl_class, self._wm_path)
        Tcl.eval(None, f"pack [ttk::frame {self._name}] -expand 1 -fill both")

        Tcl.call(None, "wm", "title", self._wm_path, title)
        Tcl.call(None, "wm", "geometry", self._wm_path, f"{width}x{height}")

        if x_type is not None and Tcl.windowing_system == "x11":
            Tcl.call(None, "wm", "attributes", self._wm_path, "-type", x_type)

        Tcl.call(None, "bind", self._name, "<Map>", self._gen_state_event)
        Tcl.call(None, "bind", self._name, "<Unmap>", self._gen_state_event)
        Tcl.call(None, "bind", self._name, "<Configure>", self._gen_state_event)
        Tcl.call(None, "update", "idletasks")

    def wait_till_closed(self) -> None:
        Tcl.call(None, "tkwait", "window", self._wm_path)

    @property
    def modal(self) -> str:
        return bool(Tcl.call(str, "wm", "transient", self._wm_path))

    @modal.setter
    def modal(self, value: bool) -> None:
        Tcl.call(None, "wm", "transient", self._wm_path, self.parent._wm_path if value else "")

        if Tcl.windowing_system == "aqua":
            Tcl.call(
                "::tk::unsupported::MacWindowStyle", "style", self._wm_path, "moveableModal", ""
            )

    def destroy(self) -> None:
        Tcl.call(None, "destroy", self)

        del self.parent._children[self._name]
        del _widgets[self._name]
