from __future__ import annotations

from enum import Enum, Flag


class Align(Enum):
    Start = 0
    End = 1
    Stretch = 2
    Center = 3


class Justify(Enum):
    Center = "center"
    Left = "left"
    Right = "right"


class Anchor(Enum):
    Bottom = "s"
    BottomLeft = "sw"
    BottomRight = "se"
    Center = "center"
    Left = "w"
    Right = "e"
    Top = "n"
    TopLeft = "nw"
    TopRight = "ne"


class ProgressMode(Enum):
    Determinate = "determinate"
    Indeterminate = "indeterminate"


class Orientation(Enum):
    Horizontal = "horizontal"
    Vertical = "vertical"


class ImagePosition(Enum):
    Below = "bottom"
    Default = "none"
    ImageOnly = "image"
    Left = "left"
    Overlap = "center"
    Right = "right"
    TextOnly = "text"
    Above = "top"

    @classmethod
    def _missing_(cls, value: object) -> ImagePosition | None:
        if value == "":
            return cls.Default


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
    def _missing_(cls, value: object) -> WindowType | None:
        if value == "":
            return cls.Normal
        return None


class Resizable(Enum):
    # TODO: These names... bleh
    Not = ("0", "0")
    Horizontal = ("1", "0")
    Vertical = ("0", "1")
    Both = ("1", "1")
