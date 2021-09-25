import os
import sys
import types
from typing import Any, Optional

import _tkinter as tk

from ._base import TukaanWidget
from ._layouts import BaseLayoutManager
from ._utils import TukaanError, from_tcl, to_tcl
from ._window_mixin import WindowMixin

tcl_interp = None


class App(WindowMixin, TukaanWidget):
    wm_path = "."
    tcl_path = ".app"

    def __init__(
        self,
        title: str = "Tukaan window",
        width: int = 200,
        height: int = 200,
        transparency: int = 1,
        topmost: bool = False,
        fullscreen: bool = False,
        theme: Optional[str] = "native",
    ) -> None:

        TukaanWidget.__init__(self)

        global tcl_interp

        if tcl_interp is self:
            raise TukaanError("can't create multiple App objects use a Window instead")

        self.app = tk.create(
            None,
            os.path.basename(sys.argv[0]),
            "Tukaan window",
            True,
            True,
            True,
            False,
            None,
        )
        self.app.loadtk()

        self.layout: BaseLayoutManager = BaseLayoutManager(self)

        tcl_interp = self

        self._tcl_call(None, "ttk::frame", ".app")
        self._tcl_call(None, "pack", ".app", "-expand", "1", "-fill", "both")

        self.title = title
        self.topmost = topmost
        self.transparency = transparency
        self.size = width, height
        self.fullscreen = fullscreen
        self.theme = theme

    def _tcl_call(self, return_type: Any, *args) -> Any:
        try:
            result = self.app.call(*map(to_tcl, args))
            if return_type is None:
                return
            return from_tcl(return_type, result)
        except tk.TclError:
            _, msg, tb = sys.exc_info()
            back_frame: types.FrameType = tb.tb_frame.f_back  # type: ignore

            back_tb = types.TracebackType(
                tb_next=None,
                tb_frame=back_frame,
                tb_lasti=back_frame.f_lasti,
                tb_lineno=back_frame.f_lineno,
            )
            raise TukaanError(msg).with_traceback(back_tb) from None

    def tcl_eval(self, return_type: Any, code: str) -> Any:
        result = self.app.eval(code)
        return from_tcl(return_type, result)

    def get_boolean(self, arg) -> bool:
        return self.app.getboolean(arg)

    def get_string(self, obj) -> str:
        if isinstance(obj, str):
            return obj

        if isinstance(obj, tk.Tcl_Obj):
            return obj.string

        return self._tcl_call(str, "format", obj)

    def split_list(self, arg) -> tuple:
        return self.app.splitlist(arg)

    def run(self) -> None:
        self.app.mainloop(0)

    def quit(self) -> None:
        """
        There is no App.destroy, just App.quit,
        which also quits the entire tcl interpreter
        """
        global tcl_interp

        for child in tuple(self._children.values()):
            child.destroy()

        self._tcl_call(None, "destroy", self.tcl_path)
        self._tcl_call(None, "destroy", self.wm_path)

        tcl_interp = None

        self.app.quit()
