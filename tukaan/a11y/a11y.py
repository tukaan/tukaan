from __future__ import annotations

from tukaan._tcl import Tcl


class Accessibility:
    @classmethod
    def allow_focus_follows_mouse(cls) -> None:
        Tcl.call(None, "tk_focusFollowsMouse")
