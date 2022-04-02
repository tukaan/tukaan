from enum import Enum


class ImagePosition(Enum):
    Bottom = "bottom"
    Default = "none"
    ImageOnly = "image"
    Left = "left"
    Overlap = "center"
    Right = "right"
    TextOnly = "text"
    Top = "top"


class Justify(Enum):
    Center = "center"
    Left = "left"
    Right = "right"


class Alignment(Enum):
    Bottom = "s"
    BottomLeft = "sw"
    BottomRight = "se"
    Center = "center"
    Default = ""
    Left = "w"
    Right = "e"
    Top = "n"
    TopLeft = "nw"
    TopRight = "ne"


class Wrap(Enum):
    Letter = "char"
    NoWrap = "none"
    Word = "word"


class CaretStyle(Enum):
    Beam = "0"
    Block = "1"


class InactiveCaretStyle(Enum):
    Hidden = "none"
    Hollow = "hollow"
    Solid = "solid"


class Resizable(Enum):
    Not = (False, False)
    Horizontal = (True, False)
    Vertical = (False, True)
    Both = (True, True)


class BackdropEffect(Enum):
    No = 0
    OpaqueColor = 1
    TransparentColor = 2
    Blur = 3
    Acrylic = 4
    Mica = 5
