import os
import sys
from typing import Any, Optional

import _tkinter as tk

from ._base import TkWidget
from ._layouts import BaseLayoutManager
from ._utils import from_tcl, to_tcl
from ._window_mixin import WindowMixin
from .exceptions import TclError

tcl_interp = None


class App(WindowMixin, TkWidget):
    wm_path = "."
    tcl_path = ".app"

    def __init__(
        self,
        title: Optional[str] = "Tukaan window",
        width: int = 200,
        height: int = 200,
        transparency: Optional[int] = None,
        topmost: Optional[bool] = None,
        fullscreen: Optional[bool] = None,
        theme: Optional[str] = "native",
    ) -> None:

        TkWidget.__init__(self)

        global tcl_interp

        if tcl_interp is self:
            raise TclError("can't create multiple App objects use a Window instead")

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
        self.tcl_interp_address = self.app.interpaddr()  # only for PIL

        self._tcl_call(None, "ttk::frame", ".app")
        self._tcl_call(None, "pack", ".app", "-expand", "1", "-fill", "both")

        if title is not None:
            self.title = title
        if topmost is not None:
            self.topmost = topmost
        if transparency is not None:
            self.transparency = transparency
        if fullscreen is not None:
            self.fullscreen = fullscreen

        self.size = width, height
        self.theme = theme

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is None:
            return self.run()
        raise exc_type(exc_value) from None

    def _tcl_call(self, return_type: Any, *args) -> Any:
        try:
            result = self.app.call(*map(to_tcl, args))
            if return_type is None:
                return
            return from_tcl(return_type, result)
        except tk.TclError:
            _, msg, tb = sys.exc_info()
            msg = str(msg)

            print(
                f"Exception in Tcl callback in {tb.tb_frame.f_back.f_code.co_filename}"
                f":{tb.tb_frame.f_back.f_lineno}",
                file=sys.stderr,
            )

            if msg.startswith("couldn't read file"):
                # FileNotFoundError is a bit more pythonic than TclError: couldn't read file
                path = msg.split('"')[1]  # path is between ""
                sys.tracebacklimit = 0
                raise FileNotFoundError(
                    f"No such file or directory: {path!r}"
                ) from None
            else:
                print(
                    f"tukaan.{TclError.__name__}: {msg}",  # tukaan.{TclError.__name__} XDD
                    file=sys.stderr,
                )
                sys.exit()

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
