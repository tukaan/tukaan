from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Union

from ._system import Platform

_cursors_win_native = {
    # Native Mappings
    "ARROW": "arrow",
    "CENTER_PTR": "center_ptr",
    "CROSSHAIR": "crosshair",
    "FLEUR": "fleur",
    "IBEAM": "ibeam",
    "ICON": "icon",
    "NONE": "none",
    "SB_H_DOUBLE_ARROW": "sb_h_double_arrow",
    "SB_V_DOUBLE_ARROW": "sb_v_double_arrow",
    "WATCH": "watch",
    "XTERM": "xterm",
    # Additional cursors
    "NO": "no",
    "STARTING": "starting",
    "SIZE": "size",
    "SIZE_NE_SW": "size_ne_sw",
    "SIZE_NS": "size_ns",
    "SIZE_NW_SE": "size_nw_se",
    "SIZE_WE": "size_we",
    "UPARROW": "uparrow",
    "WAIT": "wait",
}

_cursors_macosx_native = {
    # Native Mappings
    "ARROW": "arrow",
    "TOP_LEFT_ARROW": "top_left_arrow",
    "LEFT_PTR": "left_ptr",
    "CROSS": "cross",
    "CROSSHAIR": "crosshair",
    "TCROSS": "tcross",
    "IBEAM": "ibeam",
    "NONE": "none",
    "XTERM": "xterm",
    # Additional cursors
    "COPYARROW": "copyarrow",
    "ALIASARROW": "aliasarrow",
    "CONTEXTUALMENUARROW": "contextualmenuarrow",
    "MOVEARROW": "movearrow",
    "TEXT": "text",
    "CROSS_HAIR": "cross-hair",
    "HAND": "hand",
    "OPENHAND": "openhand",
    "CLOSEDHAND": "closedhand",
    "FIST": "fist",
    "POINTINGHAND": "pointinghand",
    "RESIZE": "resize",
    "RESIZELEFT": "resizeleft",
    "RESIZERIGHT": "resizeright",
    "RESIZELEFTRIGHT": "resizeleftright",
    "RESIZEUP": "resizeup",
    "RESIZEDOWN": "resizedown",
    "RESIZEUPDOWN": "resizeupdown",
    "RESIZEBOTTOMLEFT": "resizebottomleft",
    "RESIZETOPLEFT": "resizetopleft",
    "RESIZEBOTTOMRIGHT": "resizebottomright",
    "RESIZETOPRIGHT": "resizetopright",
    "NOTALLOWED": "notallowed",
    "POOF": "poof",
    "WAIT": "wait",
    "COUNTINGUPHAND": "countinguphand",
    "COUNTINGDOWNHAND": "countingdownhand",
    "COUNTINGUPANDDOWNHAND": "countingupanddownhand",
    "SPINNING": "spinning",
    "HELP": "help",
    "BUCKET": "bucket",
    "CANCEL": "cancel",
    "EYEDROP": "eyedrop",
    "EYEDROP_FULL": "eyedrop-full",
    "ZOOM_IN": "zoom-in",
    "ZOOM_OUT": "zoom-out",
}

_cursors_tk = {
    # Sensible included Tk cursors (subjective)
    # Some of these are native cursor mappings on Linux, some are Tk cursors
    # The docs do not specify this as with Windows or macOS
    "X_CURSOR": "X_cursor",
    "BASED_ARROW_DOWN": "based_arrow_down",
    "BASED_ARROW_UP": "based_arrow_up",
    "BOTTOM_LEFT_CORNER": "bottom_left_corner",
    "BOTTOM_RIGHT_CORNER": "bottom_right_corner",
    "BOTTOM_SIDE": "bottom_side",
    "CROSSHAIR": "crosshair",
    "DOUBLE_ARROW": "double_arrow",
    "FLEUR": "fleur",
    "HAND1": "hand1",
    "HAND2": "hand2",
    "LEFT_PTR": "left_ptr",
    "LEFT_SIDE": "left_side",
    "NONE": "none",
    "RIGHT_SIDE": "right_side",
    "SB_DOWN_ARROW": "sb_down_arrow",
    "SB_H_DOUBLE_ARROW": "sb_h_double_arrow",
    "SB_LEFT_ARROW": "sb_left_arrow",
    "SB_RIGHT_ARROW": "sb_right_arrow",
    "SB_UP_ARROW": "sb_up_arrow",
    "SB_V_DOUBLE_ARROW": "sb_v_double_arrow",
    "SIZING": "sizing",
    "TOP_LEFT_CORNER": "top_left_corner",
    "TOP_RIGHT_CORNER": "top_right_corner",
    "TOP_SIDE": "top_side",
    "WATCH": "watch",
    "XTERM": "xterm",
    # This is NOT a Tk defined cursor,
    # but the only way to set the default is with an empty string,
    # which is not a valid Enum identifier
    "DEFAULT": "",
}

# These are here if anyone wants to dig them up and use them
_cursors_tk_esoteric = {
    # Weird included Tk cursors
    # Long live gumby
    "ARROW": "arrow",
    "BOAT": "boat",
    "BOGOSITY": "bogosity",
    "BOTTOM_TEE": "bottom_tee",
    "BOX_SPIRAL": "box_spiral",
    "CENTER_PTR": "center_ptr",
    "CIRCLE": "circle",
    "CLOCK": "clock",
    "COFFEE_MUG": "coffee_mug",
    "CROSS": "cross",
    "CROSS_REVERSE": "cross_reverse",
    "DIAMOND_CROSS": "diamond_cross",
    "DOT": "dot",
    "DOTBOX": "dotbox",
    "DRAFT_LARGE": "draft_large",
    "DRAFT_SMALL": "draft_small",
    "DRAPED_BOX": "draped_box",
    "EXCHANGE": "exchange",
    "GOBBLER": "gobbler",
    "GUMBY": "gumby",
    "HEART": "heart",
    "ICON": "icon",
    "IRON_CROSS": "iron_cross",
    "LEFT_TEE": "left_tee",
    "LEFTBUTTON": "leftbutton",
    "LL_ANGLE": "ll_angle",
    "LR_ANGLE": "lr_angle",
    "MAN": "man",
    "MIDDLEBUTTON": "middlebutton",
    "MOUSE": "mouse",
    "PENCIL": "pencil",
    "PIRATE": "pirate",
    "PLUS": "plus",
    "QUESTION_ARROW": "question_arrow",
    "RIGHT_PTR": "right_ptr",
    "RIGHT_TEE": "right_tee",
    "RIGHTBUTTON": "rightbutton",
    "RTL_LOGO": "rtl_logo",
    "SAILBOAT": "sailboat",
    "SHUTTLE": "shuttle",
    "SPIDER": "spider",
    "SPRAYCAN": "spraycan",
    "STAR": "star",
    "TARGET": "target",
    "TCROSS": "tcross",
    "TOP_LEFT_ARROW": "top_left_arrow",
    "TOP_TEE": "top_tee",
    "TREK": "trek",
    "UL_ANGLE": "ul_angle",
    "UMBRELLA": "umbrella",
    "UR_ANGLE": "ur_angle",
}
_CursorsEsoteric = Enum("CursorsEsoteric", _cursors_tk_esoteric)

if Platform.os == "Window":
    Cursors = Enum("Cursors", _cursors_tk | _cursors_win_native)
elif Platform.os == "macOS":
    Cursors = Enum("Cursors", _cursors_tk | _cursors_macosx_native)
else:
    Cursors = Enum("Cursors", _cursors_tk)


class Cursor:
    @Platform.windows_only
    def __init__(self, source: Path):
        # Actually accepts any pathlike object
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(f"Cursor file {src!s} does not exist")
        filetype = src.suffix
        if filetype not in (".ani", ".cur"):
            raise ValueError(f'Bad file type for Windows cursor: "{filetype}". Should be one of ".cur" or ".ani"')
        self.source = "@" + str(source)

    @Platform.windows_only
    def __to_tcl__(self) -> str:
        return self.source

    @classmethod
    @Platform.windows_only
    def __from_tcl__(cls, value) -> Cursor:
        return Cursor(value)


Cursor_T = Union[Cursors, Cursor]
