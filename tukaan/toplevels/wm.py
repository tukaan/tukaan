from __future__ import annotations

import functools
import re
import sys
from fractions import Fraction
from typing import Callable

from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan.enums import Resizable, WindowState, WindowType
from tukaan.errors import TclCallError


class WindowGeometryManager:
    _toplevel_name: str

    @Tcl.redraw_before
    def _get_geometry(self) -> tuple[int, ...]:
        return tuple(
            map(int, re.split(r"x|\+", Tcl.call(str, "wm", "geometry", self._toplevel_name)))
        )

    @property
    def x(self) -> int:
        """Get or set the position of this window on the x axis."""
        return self._get_geometry()[2]

    @x.setter
    @Tcl.redraw_after
    def x(self, value: int) -> None:
        Tcl.call(None, "wm", "geometry", self._toplevel_name, f"+{value}+{self.y}")

    @property
    def y(self) -> int:
        """Get or set the position of this window on the y axis."""
        return self._get_geometry()[3]

    @y.setter
    @Tcl.redraw_after
    def y(self, value: int) -> None:
        Tcl.call(None, "wm", "geometry", self._toplevel_name, f"+{self.x}+{value}")

    @property
    @Tcl.redraw_before
    def position(self) -> tuple[int, ...]:
        return self._get_geometry()[2:]

    @position.setter
    @Tcl.redraw_after
    def position(self, value: tuple[int, ...] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._toplevel_name, "+{}+{}".format(*value))

    @property
    def width(self) -> int:
        """Get or set the width of this window."""
        return self._get_geometry()[0]

    @width.setter
    @Tcl.redraw_after
    def width(self, value: int) -> None:
        Tcl.call(None, "wm", "geometry", self._toplevel_name, f"{value}x{self.height}")

    @property
    def height(self) -> int:
        """Get or set the height of this window."""
        return self._get_geometry()[1]

    @height.setter
    @Tcl.redraw_after
    def height(self, value: int) -> None:
        Tcl.call(None, "wm", "geometry", self._toplevel_name, f"{self.width}x{value}")

    @property
    @Tcl.redraw_before
    def size(self) -> tuple[int, ...]:
        return self._get_geometry()[:2]

    @size.setter
    @Tcl.redraw_after
    def size(self, value: tuple[int, ...] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "geometry", self._toplevel_name, "{}x{}".format(*value))

    @property
    @Tcl.redraw_before
    def min_size(self) -> tuple[int, ...]:
        return Tcl.call((int,), "wm", "minsize", self._toplevel_name)

    @min_size.setter
    @Tcl.redraw_after
    def min_size(self, value: tuple[int, ...] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "minsize", self._toplevel_name, *value)

    @property
    @Tcl.redraw_before
    def max_size(self) -> tuple[int, ...]:
        return Tcl.call((int,), "wm", "maxsize", self._toplevel_name)

    @max_size.setter
    @Tcl.redraw_after
    def max_size(self, value: tuple[int, ...] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "maxsize", self._toplevel_name, *value)

    @property
    def resizable(self) -> Resizable:
        return Resizable(Tcl.call((str,), "wm", "resizable", self._toplevel_name))

    @resizable.setter
    def resizable(self, value: Resizable) -> None:
        Tcl.call(None, "wm", "resizable", self._toplevel_name, *value.value)

    @property
    def size_increment(self) -> tuple[int, ...]:
        return Tcl.call((int,), "wm", "grid", self._toplevel_name)[2:]

    @size_increment.setter
    def size_increment(self, value: tuple[int, ...] | int) -> None:
        if isinstance(value, int):
            value = (value,) * 2

        Tcl.call(None, "wm", "grid", self._toplevel_name, 1, 1, *value)


class WindowStateManager:
    _toplevel_name: str
    bind: Callable
    unbind: Callable

    _current_state = "normal"

    def _get_state(self) -> str:
        try:
            state = Tcl.call(str, "wm", "state", self._toplevel_name)
        except TclCallError:
            return "closed"

        if Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-fullscreen"):
            return "fullscreen"
        elif state == "normal" and Platform.window_sys == "x11":
            # needs further checks on X11
            if Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-zoomed"):
                return "zoomed"
        return state

    def _gen_state_event(self):
        prev_state = self._current_state
        new_state = self._get_state()

        if new_state == prev_state:
            return

        events = ["<<StateChanged>>"]

        if new_state == "normal":
            events.append("<<Restore>>")
        elif new_state == "zoomed":
            events.append("<<Maximize>>")
        elif new_state == "iconic":
            events.append("<<Minimize>>")
        elif new_state == "withdrawn":
            events.append("<<Hide>>")
        elif new_state == "fullscreen":
            events.append("<<Fullscreen>>")

        if prev_state == "zoomed":
            events.append("<<Unmaximize>>")
        elif prev_state == "iconic":
            events.append("<<Unminimize>>")
        elif prev_state == "withdrawn":
            events.append("<<Unhide>>")
        elif prev_state == "fullscreen":
            events.append("<<Unfullscreen>>")

        for event in events:
            Tcl.eval(None, f"event generate .app {event}")  # TODO: not .app

        self._current_state = new_state

    def minimize(self) -> None:
        """Hide this window from the screen, and collapse it to an icon."""
        Tcl.call(None, "wm", "iconify", self._toplevel_name)

    def maximize(self) -> None:
        """
        Resize this window fill up all available space.
        Note, that this doesn't necessarily mean the entire screen.
        """
        if Platform.window_sys == "x11":
            Tcl.call(None, "wm", "attributes", self._toplevel_name, "-zoomed", True)
        else:
            Tcl.call(None, "wm", "state", self._toplevel_name, "zoomed")

    def go_fullscreen(self) -> None:
        """Make the window fill up the entire screen."""
        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-fullscreen", True)

    def exit_fullscreen(self) -> None:
        """Exit full screen mode."""
        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-fullscreen", False)

    def restore(self) -> None:
        """
        Make this window normal size.
        If it's maximized, minimized or withdrawn, makes it visible,
        and resizes it to normal size. If it's in full screen mode, resets it
        to the state it was in before going full screen.
        """
        state = self._get_state()

        if state in ("withdrawn", "iconic"):
            Tcl.call(None, "wm", "deiconify", self._toplevel_name)
        elif state == "zoomed":
            if Platform.window_sys == "x11":
                Tcl.call(None, "wm", "attributes", self._toplevel_name, "-zoomed", False)
            else:
                Tcl.call(None, "wm", "state", self._toplevel_name, "normal")
        elif state == "fullscreen":
            Tcl.call(None, "wm", "attributes", self._toplevel_name, "-fullscreen", False)

    def hide(self) -> None:
        """
        Hide this window and its icon from the screen.
        On macOS this does not seem to hide the window icon.
        """
        Tcl.call(None, "wm", "withdraw", self._toplevel_name)

    def unhide(self) -> None:
        """Restore this window if it's hidden."""
        Tcl.call(None, "wm", "deiconify", self._toplevel_name)

    def request_attention(self, force: bool = False) -> None:
        """
        Tell the window manager, that this window wants attention.
        Note that depending on the window manager, this may not necessarily result
        in the window being focused.
        """
        if force:
            Tcl.call(None, "focus", self._toplevel_name)
        else:
            Tcl.call(None, "focus", "-force", self._toplevel_name)

    @property
    def state(self) -> WindowState:
        """Return the current state of this window. See also :class:`tukaan.enums.WindowState`"""
        return WindowState(self._get_state())

    @property
    def focused(self) -> bool:
        """Return whether this window currently has input focus."""
        return Tcl.call(str, "focus", "-displayof", self._toplevel_name) == self._toplevel_name

    @property
    @Tcl.redraw_before
    def visible(self) -> bool:
        """Return whether this window is currently visible on the screen or not."""
        return Tcl.call(bool, "winfo", "viewable", self._toplevel_name)

    @property
    def always_on_top(self) -> bool:
        """
        Get or set whether this window should always stay on top of
        other windows, even if it isn't in focus.
        """
        return Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-topmost")

    @always_on_top.setter
    @Tcl.redraw_before
    def always_on_top(self, value: bool) -> None:
        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-topmost", value)


class WindowDecorationManager:
    _toplevel_name: str
    hwnd: int

    @property
    def title(self) -> str:
        """
        Get or set the title of this window. It usually appears in the
        title bar of the window (if it has one), and next to the taskbar/panel icon.
        """
        return Tcl.call(str, "wm", "title", self._toplevel_name)

    @title.setter
    def title(self, value: str) -> None:
        Tcl.call(None, "wm", "title", self._toplevel_name, value or "")

    @property
    def opacity(self) -> float:
        """Get or set the opacity of this window."""
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
        """
        Get or set whether something inside the window has been modified,
        for example if a document is 'dirty'.
        On macOS this means displaying a dot inside the close button of the window.
        """
        return Tcl.call(bool, "wm", "attributes", self._toplevel_name, "-modified")

    @dirty.setter
    @Platform.macOS_only
    def dirty(self, value: bool) -> None:
        Tcl.call(None, "wm", "attributes", self._toplevel_name, "-modified", value)

    @property
    @Platform.windows_only
    def dark_themed_titlebar(self) -> bool:
        """
        Get or set whether this window should have a dark themed titlebar.
        This attribute doesn't do anything below Windows 11 build 22000, and on other operating systems.
        """
        import ctypes

        if sys.getwindowsversion().build < 22000:  # type: ignore
            return False

        c_value = ctypes.c_int()

        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            self.hwnd,
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.byref(c_value),
            ctypes.sizeof(ctypes.c_int),
        )
        return bool(c_value)

    @dark_themed_titlebar.setter
    @Platform.windows_only
    def dark_themed_titlebar(self, value: bool) -> None:
        import ctypes

        if sys.getwindowsversion().build < 22000:  # type: ignore
            return

        c_value = ctypes.c_int(int(value))

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            self.hwnd,
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.byref(c_value),
            ctypes.sizeof(ctypes.c_int),
        )


class WindowManager(WindowGeometryManager, WindowStateManager, WindowDecorationManager):
    _toplevel_name: str
    destroy: Callable[[], None]

    @property
    def type(self) -> WindowType:
        """
        Get or set the purpose of this window. Most window managers use this property
        to appropriately set decorations and animations for the window.

        For example a utility window usually only has a close button, and a
        splash window would be placed in the center of the screen, without decorations.

        See also :class:`tukaan.enums.WindowType`
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
