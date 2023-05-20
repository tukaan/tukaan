from __future__ import annotations

from enum import Enum, Flag


class Align(Enum):
    Start = 0
    End = 1
    Stretch = 2
    Center = 3


class WindowState(Enum):
    Closed = "closed"
    FullScreen = "fullscreen"
    Hidden = "withdrawn"
    Maximized = "zoomed"
    Minimized = "iconic"
    Normal = "normal"


class WindowType(Enum):
    Combo = "combo"
    Desktop = "desktop"
    Dialog = "dialog"
    DnD = "dnd"
    Dock = "dock"
    DropdownMenu = "dropdown_menu"
    Menu = "menu"
    Normal = "normal"
    Notification = "notification"
    PopupMenu = "popup_menu"
    Splash = "splash"
    ToolBar = "toolbar"
    ToolTip = "tooltip"
    ToolWindow = "toolwindow"
    Utility = "utility"

    @classmethod
    def _missing_(cls, value: str) -> WindowType | None:
        if value == "":
            return cls.Normal


class Resizable(Enum):
    # TODO: These names... bleh
    Not = ("0", "0")
    Horizontal = ("1", "0")
    Vertical = ("0", "1")
    Both = ("1", "1")
