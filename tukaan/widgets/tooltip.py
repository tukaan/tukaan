from __future__ import annotations

from typing import TYPE_CHECKING

from tukaan._tcl import Tcl
from tukaan.exceptions import TukaanTclError

if TYPE_CHECKING:
    from tukaan._base import WidgetBase


class ToolTipProvider:
    _widgets: dict[str, str | None] = {}
    _schedule_cmd: str = ""
    _hide_cmd: str = ""
    _show_cmd: str = ""
    _setup_done = False
    _after_id: str = ""
    _can_show = True

    @classmethod
    def setup(cls) -> None:
        cls._schedule_cmd = Tcl.to(cls.schedule)
        cls._hide_cmd = Tcl.to(cls.hide)
        cls._show_cmd = Tcl.to(cls.show)

        Tcl.call(None, "toplevel", ".tooltip")
        Tcl.call(None, "wm", "withdraw", ".tooltip")
        Tcl.eval(None, "pack [ttk::label .tooltip.label -style Tooltip] -expand 1 -fill both")
        Tcl.call(None, "wm", "overrideredirect", ".tooltip", 1)

        if Tcl.call(str, "tk", "windowingsystem") == "x11":
            Tcl.call(None, "wm", "attributes", ".tooltip", "-type", "tooltip")

        cls._setup_done = True

    @classmethod
    def add(cls, owner: WidgetBase, message: str | None) -> None:
        if not cls._setup_done:
            cls.setup()

        cls._widgets[owner._lm_path] = message

        Tcl.call(None, "bind", owner._lm_path, "<Enter>", f"+ {cls._schedule_cmd} %W")
        Tcl.call(None, "bind", owner._lm_path, "<Leave>", f"+ {cls._hide_cmd}")
        Tcl.call(None, "bind", owner._lm_path, "<ButtonPress>", f"+ {cls._hide_cmd}")

    @classmethod
    def update(cls, owner: WidgetBase, message: str | None) -> None:
        if owner._lm_path not in cls._widgets and message:
            return cls.add(owner, message)

        cls._widgets[owner._lm_path] = message

    @classmethod
    def get(cls, owner: WidgetBase) -> str | None:
        return cls._widgets.get(owner._lm_path)

    @classmethod
    def schedule(cls, widget: str) -> None:
        cls._can_show = True

        message = cls._widgets.get(widget)
        if message is None:
            return

        Tcl.call(None, ".tooltip.label", "configure", "-text", message)
        cls._after_id = Tcl.call(str, "after", 650, cls._show_cmd, widget, len(message.split(" ")))

    @classmethod
    def hide(cls) -> None:
        cls._can_show = False  # after cancel sometime doesn't work, so this is a hack

        Tcl.call(None, "after", "cancel", cls._show_cmd)
        Tcl.call(None, "after", "cancel", cls._hide_cmd)
        Tcl.call(None, "wm", "withdraw", ".tooltip")

    @classmethod
    def show(cls, widget: str, length: str) -> None:
        if not cls._can_show:
            return

        owner_x = Tcl.call(int, "winfo", "rootx", widget)
        owner_width = Tcl.call(int, "winfo", "reqwidth", widget)
        tip_width = Tcl.call(int, "winfo", "reqwidth", ".tooltip")
        tip_x = owner_x + owner_width // 2 - tip_width // 2

        if tip_x <= Tcl.eval(int, f"winfo rootx [winfo toplevel {widget}]"):
            tip_x = owner_x

        owner_y = Tcl.call(int, "winfo", "rooty", widget)
        tip_height = Tcl.call(int, "winfo", "reqheight", ".tooltip")
        tip_y = owner_y - tip_height - 5

        if tip_y <= Tcl.eval(int, f"winfo rooty [winfo toplevel {widget}]"):
            tip_y = owner_y + Tcl.call(int, "winfo", "reqheight", widget) + 5

        Tcl.call(None, "wm", "geometry", ".tooltip", f"+{tip_x}+{tip_y}")
        Tcl.call(None, "wm", "deiconify", ".tooltip")

        hide_after = (round(60 / 260 * int(length)) or 1) * 10000  # Very intelligent

        Tcl.call(str, "after", hide_after, cls._hide_cmd)
