from __future__ import annotations

from enum import Enum
from typing import Union

from tukaan._system import Platform
from tukaan._typing import Literal


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
    def _missing_(cls, value: object) -> ImagePosition | None:
        if value == "":
            return cls.Default
        return None


ImagePositionType = Union[
    ImagePosition, Literal["bottom", "none", "image", "left", "center", "right", "text", "top"]
]


class Justify(Enum):
    Center = "center"
    Left = "left"
    Right = "right"


JustifyType = Union[Justify, Literal["center", "left", "right"]]


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


AnchorType = Union[Anchor, Literal["s", "sw", "se", "center", "w", "e", "n", "nw", "ne"]]


class ProgressMode(Enum):
    Determinate = "determinate"
    Indeterminate = "indeterminate"


ProgressModeType = Union[ProgressMode, Literal["determinate", "indeterminate"]]


class Orientation(Enum):
    Horizontal = "horizontal"
    Vertical = "vertical"


OrientationType = Union[Orientation, Literal["horizontal", "vertical"]]


class EventQueue(Enum):
    First = "head"
    Last = "tail"
    Immediate = "now"
    AfterPrevious = "mark"


EventQueueType = Union[EventQueue, Literal["head", "tail", "now", "mark"]]

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
    Maximized = "zoomed"
    Minimized = "iconic"
    Normal = "normal"


WindowStateType = Union[
    WindowState, Literal["closed", "fullscreen", "withdrawn", "maximized", "minimized", "normal"]
]


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
    ToolWindow = "toolwindow"
    Utility = "utility"


WindowTypeKind = Union[
    WindowType,
    Literal[
        "combo",
        "desktop",
        "dialog",
        "dnd",
        "dock",
        "dropdown_menu",
        "normal",
        "notification",
        "popup_menu",
        "splash",
        "toolbar",
        "tooltip",
        "toolwindow",
        "utility",
    ],
]


_cursors_tk = {
    # Most of these are native cursor mappings on Linux,
    # and fall back to basic X11 ones
    #
    # General
    "Arrow": "arrow",
    "RightArrow": "right_ptr",
    "UpArrow": "center_ptr",
    "Blank": "none",
    # Link & Status
    "Forbidden": "circle",
    "Help": "question_arrow",
    "Wait": "watch",
    "Progress": "watch",
    "PointingHand": "hand2",
    # Selection
    "Crosshair": "crosshair",
    "Bullseye": "dotbox",
    "Text": "xterm",
    # Resize
    "Move": "fleur",
    "UpResize": "top_side",
    "DownResize": "bottom_side",
    "RightResize": "right_side",
    "LeftResize": "left_side",
    "HorResize": "sb_h_double_arrow",
    "VertResize": "sb_v_double_arrow",
    "NwSeResize": "sizing",  # TODO: better idea?
    "NeSwResize": "sizing",
    "TopRightResize": "top_right_corner",
    "TopLeftResize": "top_left_corner",
    "BottomRightResize": "bottom_right_corner",
    "BottomLeftResize": "bottom_left_corner",
    # Drag and drop
    "DragLink": "left_ptr",  # TODO
    "DragCopy": "left_ptr",  # TODO
    "Grab": "hand2",
    "Grabbing": "fleur",
    # Additional cursors
    "Cell": "plus",
    "Pencil": "pencil",
    "Eyedrop": "crosshair",
}

_cursors_macos_native = {
    "Forbidden": "notallowed",
    "Wait": "wait",
    "Progress": "spinning",
    "PointingHand": "pointinghand",
    "Text": "text",
    "DragLink": "aliasarrow",
    "DragCopy": "copyarrow",
    "Grab": "openhand",
    "Grabbing": "closedhand",
    "Eyedrop": "eyedrop",
}

_cursors_win_native = {
    "UpArrow": "uparrow",
    "Forbidden": "no",
    "Wait": "wait",
    "Progress": "starting",
    "Text": "ibeam",
    "Move": "size",
    "HorResize": "size_we",
    "VertResize": "size_ns",
    "NwSeResize": "size_nw_se",
    "NeSwResize": "size_ne_sw",
}


if Platform.os == "Windows":
    _cursors_tk.update(_cursors_win_native)
elif Platform.os == "macOS":
    _cursors_tk.update(_cursors_macos_native)

Cursor = Enum("Cursors", _cursors_tk)


@classmethod
def _cursor_missing_(cls, value: str) -> Cursor:
    if value == "":
        return cls.Arrow
    elif value in ("xterm", "ibeam", "text"):
        return cls.Text
    return None


Cursor._missing_ = _cursor_missing_


class LegacyX11Cursor(Enum):
    BasedArrowDown = "based_arrow_down"
    BasedArrowUp = "based_arrow_up"
    Boat = "boat"
    Bogosity = "bogosity"
    BoxSpiral = "box_spiral"
    Clock = "clock"
    CoffeeMug = "coffee_mug"
    DiamondCross = "diamond_cross"
    Dot = "dot"
    DrapedBox = "draped_box"
    Exchange = "exchange"
    Gobbler = "gobbler"
    Gumby = "gumby"
    Hand1 = "hand1"
    Heart = "heart"
    Icon = "icon"
    IronCross = "iron_cross"
    LeftButton = "leftbutton"
    Man = "man"
    MiddleButton = "middlebutton"
    Mouse = "mouse"
    Pirate = "pirate"
    RightButton = "rightbutton"
    RtlLogo = "rtl_logo"
    Sailboat = "sailboat"
    Shuttle = "shuttle"
    Spider = "spider"
    Spraycan = "spraycan"
    Star = "star"
    Trek = "trek"
    Umbrella = "umbrella"
    X = "X_cursor"
