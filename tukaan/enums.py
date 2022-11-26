from __future__ import annotations

from enum import Enum


class Align(Enum):
    Start = 0
    End = 1
    Stretch = 2


class ImagePosition(Enum):
    Bottom = "bottom"
    Default = "none"
    ImageOnly = "image"
    Left = "left"
    Overlap = "center"
    Right = "right"
    TextOnly = "text"
    Top = "top"

    @classmethod
    def _missing_(cls, value) -> ImagePosition:
        if value == "":
            return cls.Default


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


class EventQueue(Enum):
    First = "head"
    Last = "tail"
    Immediate = "now"
    AfterPrevious = "mark"


# class Location(Enum):
#    ...
#
#
# class Direction(Enum):
#    ...
#
#
# class Wrap(Enum):
#    Letter = "char"
#    NoWrap = "none"
#    Word = "word"
#
#
# class CaretStyle(Enum):
#    Beam = "0"
#    Block = "1"
#
#
# class InactiveCaretStyle(Enum):
#    Hidden = "none"
#    Hollow = "hollow"
#    Solid = "solid"


class Resizable(Enum):
    Not = ("0", "0")
    Horizontal = ("1", "0")
    Vertical = ("0", "1")
    Both = ("1", "1")


class WindowState(Enum):
    Closed = "closed"
    FullScreen = "fullscreen"
    Hidden = "withdrawn"
    Maximized = "maximized"
    Minimized = "minimized"
    Normal = "normal"


class WindowType(Enum):
    Combo = "combo"
    Desktop = "desktop"
    Dialog = "dialog"
    DnD = "dnd"
    Dock = "dock"
    DropDown = "dropdown_menu"
    Menu = "menu"
    Normal = "normal"
    Notification = "notification"
    PopupMenu = "popup_menu"
    Splash = "splash"
    ToolBar = "toolbar"
    Tooltip = "tooltip"
    Utility = "utility"


class WindowBackdropType(Enum):
    Normal = 1
    Mica = 2
    Acrylic = 3
    MicaAlt = 4
