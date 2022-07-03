from __future__ import annotations

from typing import TYPE_CHECKING

from tukaan._tcl import Tcl
from tukaan.exceptions import TclError

if TYPE_CHECKING:
    from tukaan._base import WidgetBase


class ToolTipProvider:
    _widgets: dict[str, str] = {}
    _schedule_cmd: str = ""
    _hide_cmd: str = ""
    _show_cmd: str = ""
    _setup_done = False
    _after_id: str = ""

    @classmethod
    def setup(cls) -> None:
        cls._schedule_cmd = Tcl.to(cls.schedule)
        cls._hide_cmd = Tcl.to(cls.hide)
        cls._show_cmd = Tcl.to(cls.show)

        try:
            Tcl.eval(None, "ttk::style layout ToolTip")
        except TclError:
            style = "TButton"
        else:
            style = "ToolTip"

        Tcl.call(None, "toplevel", ".tooltip")
        Tcl.call(None, "wm", "withdraw", ".tooltip")
        Tcl.eval(None, f"pack [ttk::label .tooltip.label -style {style}] -expand 1 -fill both")
        Tcl.call(None, "wm", "overrideredirect", ".tooltip", 1)

    @classmethod
    def add(cls, owner: WidgetBase, message: str) -> None:
        if not cls._setup_done:
            cls.setup()

        cls._widgets[owner._lm_path] = message

        Tcl.call(None, "bind", owner._lm_path, "<Enter>", f"+ {cls._schedule_cmd} %W")
        Tcl.call(None, "bind", owner._lm_path, "<Leave>", f"+ {cls._hide_cmd}")
        Tcl.call(None, "bind", owner._lm_path, "<ButtonPress>", f"+ {cls._hide_cmd}")

    @classmethod
    def schedule(cls, widget: str) -> None:
        message = cls._widgets.get(widget)
        if message is None:
            return

        Tcl.call(None, ".tooltip.label", "configure", "-text", message)
        cls._after_id = Tcl.call(str, "after", 1000, cls._show_cmd, widget)

    @classmethod
    def hide(cls) -> None:
        Tcl.call(None, "after", "cancel", cls._show_cmd)
        Tcl.call(None, "after", "cancel", cls._hide_cmd)
        Tcl.call(None, "wm", "withdraw", ".tooltip")

    @classmethod
    def show(cls, widget: str) -> None:
        owner_x = Tcl.call(int, "winfo", "rootx", widget)
        owner_width = Tcl.call(int, "winfo", "reqwidth", widget)
        tip_width = Tcl.call(int, "winfo", "reqwidth", ".tooltip")
        tip_x = owner_x + owner_width // 2 - tip_width // 2

        owner_y = Tcl.call(int, "winfo", "rooty", widget)
        tip_height = Tcl.call(int, "winfo", "reqheight", ".tooltip")
        tip_y = owner_y - tip_height - 5

        if tip_y <= Tcl.call(int, "winfo", "rooty", ".app"):
            tip_y = owner_y + Tcl.call(int, "winfo", "reqheight", widget) + 5

        Tcl.call(None, "wm", "geometry", ".tooltip", f"+{tip_x}+{tip_y}")
        Tcl.call(None, "wm", "deiconify", ".tooltip")

        Tcl.call(str, "after", 10000, cls._hide_cmd)
