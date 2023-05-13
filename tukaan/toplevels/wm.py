from __future__ import annotations

import functools
from typing import Callable

from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan.enums import WindowType


class WindowDecorationManager:
    # These aren't necessarily related to the window decoration

    _toplevel_name: str

    @property
    def title(self) -> str:
        return Tcl.call(str, "wm", "title", self._toplevel_name)

    @title.setter
    def title(self, value: str) -> None:
        Tcl.call(None, "wm", "title", self._toplevel_name, value or "")

    @property
    def opacity(self) -> float:
        return Tcl.call(float, "wm", "attributes", self._toplevel_name, "-alpha")

    @opacity.setter
    @Tcl.redraw_after
    def opacity(self, value: float) -> None:
        if Platform.window_sys == "x11":
            Tcl.call(None, "tkwait", "visibility", self._toplevel_name)

        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-alpha", value)

    @property
    @Platform.macOS_only
    def dirty(self) -> bool:
        return Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-modified")

    @dirty.setter
    @Platform.macOS_only
    def dirty(self, value: bool) -> None:
        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-modified", value)


class WindowManager(WindowDecorationManager):
    _toplevel_name: str
    destroy: Callable[[], None]

    @property
    def type(self) -> WindowType:
        """
        Set the purpose of this window. Most window managers use this property
        to appropriately set decorations and animations for the window.

        For example a utility window usually only has a close button, and a
        splash window would be placed in the center of the screen, without decorations.
        """
        if Platform.window_sys == "win32":
            if Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-toolwindow"):
                return WindowType.Utility
            return WindowType.Normal
        elif Platform.window_sys == "x11":
            return Tcl.call(WindowType, "wm", "attributes", self._toplevel_name, "-type")
        return WindowType.Normal

    @type.setter
    def type(self, value: WindowType) -> None:
        if Platform.window_sys == "win32":
            if value is WindowType.Utility:
                Tcl.call(None, "wm", "attributes", self._toplevel_name, "-toolwindow", True)
            elif value is WindowType.Normal:
                Tcl.call(None, "wm", "attributes", self._toplevel_name, "-toolwindow", False)
        elif Platform.window_sys == "x11":
            Tcl.call(None, "wm", "attributes", self._toplevel_name, "-type", value)

    def group(self, other: WindowManager) -> None:
        """
        Groups this window with another toplevel window. Grouped windows are managed together
        (i.e., minimized and deminimized together, possibly kept together in the stacking order, etc.),
        but it is up to the window manager to determine; this is formally just a hint.
        """
        Tcl.call(None, "wm", "group", self._toplevel_name, other._toplevel_name)

    def on_close(self, func: Callable[[WindowManager], bool]) -> Callable[[], None]:
        """
        A function decorated with this method will be called when the window manager
        asks the window to close itself (for example when clicking on the close button
        in the titlebar, or pressing Alt+F4 on Windows).

        The return value of the function indicates whether the window can be safely closed,
        and returning `True` will destroy the window.

        The function shouléd take exactly one argument, which is the window instance to be closed.
        """

        @functools.wraps(func)
        def wrapper() -> None:
            if func(self):
                self.destroy()

        Tcl.call(None, "wm", "protocol", self._toplevel_name, "WM_DELETE_WINDOW", wrapper)
        return wrapper

    @property
    def id(self) -> int:
        return Tcl.call(int, "winfo", "id", self._toplevel_name)

    @property
    def hwnd(self) -> int:
        return Tcl.call(int, "wm", "frame", self._toplevel_name)

    @property
    def class_name(self) -> str:
        return Tcl.call(str, "winfo", "class", self._toplevel_name)
