from __future__ import annotations

from tukaan._base import WindowBase, generate_pathname
from tukaan._tcl import Tcl
from tukaan._utils import _widgets
from tukaan.app import App


class Window(WindowBase):
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
    ) -> None:
        assert isinstance(parent, WindowBase), "Window parent must be an App or a Window"

        self._wm_path = generate_pathname(self, parent)
        self._name = self._lm_path = f"{self._wm_path}.frame"
        self.parent = parent
        self.parent._children[self._name] = self

        super().__init__()

        Tcl.call(None, self._tcl_class, self._wm_path)
        Tcl.eval(None, f"pack [ttk::frame {self._name}] -expand 1 -fill both")

        self._set_title(title)
        self._set_size((width, height))

        Tcl.call(None, "bind", self, "<Map>", self._generate_state_event)
        Tcl.call(None, "bind", self, "<Unmap>", self._generate_state_event)
        Tcl.call(None, "bind", self, "<Configure>", self._generate_state_event)

    def wait_till_closed(self) -> None:
        Tcl.call(None, "tkwait", "window", self._wm_path)

    def destroy(self) -> None:
        Tcl.call(None, "destroy", self)

        del self.parent._children[self._name]
        del _widgets[self._name]
