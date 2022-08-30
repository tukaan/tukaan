from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from tukaan.fonts.font import Font

from ._structures import TabStop
from ._tcl import Tcl
from ._utils import _commands, seq_pairs
from ._variables import ControlVariable
from .colors import Color
from .enums import ImagePosition, Justify, Orientation

if TYPE_CHECKING:
    from ._base import TkWidget


def config(widget: TkWidget, **kwargs) -> None:
    Tcl.call(None, widget, "configure", *Tcl.to_tcl_args(**kwargs))


def cget(widget: TkWidget, return_type: Any, option: str) -> Any:
    return Tcl.call(return_type, widget, "cget", option)


def get_image_pos(self) -> ImagePosition:
    return cget(self, ImagePosition, "-compound")


def set_image_pos(self, value: ImagePosition) -> None:
    config(self, compound=value)


image_pos = property(get_image_pos, set_image_pos)


def get_text_align(self) -> Justify:
    return cget(self, Justify, "-justify")


def set_text_align(self, value: Justify) -> None:
    config(self, justify=value)


text_align = property(get_text_align, set_text_align)


def get_fg_color(self) -> Color:
    return cget(self, Color, "-foreground")


def set_fg_color(self, value: Color | str) -> None:
    config(self, foreground=value)


fg_color = property(get_fg_color, set_fg_color)


def get_bg_color(self) -> Color:
    return cget(self, Color, "-foreground")


def set_bg_color(self, value: Color | str) -> None:
    config(self, foreground=value)


bg_color = property(get_bg_color, set_bg_color)


def get_text(self) -> str:
    return cget(self, str, "-text")


def set_text(self, value: str) -> None:
    config(self, text=value)


text = property(get_text, set_text)


def get_width(self) -> int:
    return cget(self, int, "-width")


def set_width(self, value: int) -> None:
    config(self, width=value)


width = property(get_width, set_width)


def get_height(self) -> int:
    return cget(self, int, "-height")


def set_height(self, value: int) -> None:
    config(self, height=value)


height = property(get_height, set_height)


def get_command(self) -> Callable | None:
    return _commands.get(cget(self, str, "-command"))


def set_command(self, func: Callable | None) -> None:
    value = func
    if value is None:
        value = ""
    config(self, command=value)


command = property(get_command, set_command)


def get_orientation(self) -> Orientation:
    return cget(self, Orientation, "-orient")


def set_orientation(self, value: Orientation) -> None:
    return config(self, orient=value)


orientation = property(get_orientation, set_orientation)


def get_value(self) -> int:
    return cget(self, int, "-value")


def set_value(self, value: int) -> None:
    return config(self, value=value)


value = property(get_value, set_value)


def get_font(self) -> Font | dict[str, str | int | bool]:
    return cget(self, Font, "-font")


def set_font(self, font: Font | dict[str, str | int | bool]) -> None:
    return config(self, font=font)


font = property(get_font, set_font)


def get_link(self) -> ControlVariable:
    return cget(self, ControlVariable, "-variable")


def set_link(self, value: ControlVariable | None) -> None:
    self._variable = value

    if value is None:
        value = ""  # type: ignore
    return config(self, variable=value)


link = property(get_link, set_link)


def get_focusable(self) -> bool:
    return cget(self, bool, "-takefocus")


def set_focusable(self, value: bool) -> None:
    config(self, takefocus=value)


focusable = property(get_focusable, set_focusable)


def get_tab_stops(self) -> list[TabStop]:
    return [TabStop(pos, align) for pos, align in seq_pairs(cget(self, [str], "-tabs"))]


def set_tab_stops(self, tab_stops: TabStop | list[TabStop]) -> None:
    if tab_stops is None:
        return

    if isinstance(tab_stops, TabStop):
        tab_stops = [tab_stops]

    config(self, tabs=[y for x in tab_stops for y in x.__to_tcl__()])


tab_stops = property(get_tab_stops, set_tab_stops)


def _convert_padding(padding: int | tuple[int, ...] | None) -> tuple | tuple[int, ...] | str:
    if padding is None:
        return ()
    elif isinstance(padding, int):
        return (value,) * 4
    else:
        length = len(padding)
        if length == 1:
            return padding * 4
        elif length == 2:
            return (padding[1], padding[0], padding[1], padding[0])
        elif length == 3:
            return (padding[1], padding[0], padding[1], padding[2])
        elif length == 4:
            return (padding[3], padding[0], padding[1], padding[2])
        else:
            return ""


def _convert_padding_back(padding) -> tuple[int, int, int, int]:
    if len(padding) == 1:
        return (padding[0],) * 4
    elif len(padding) == 4:
        return (padding[1], padding[2], padding[3], padding[0])

    return (0,) * 4


def get_padding(self) -> tuple[int, int, int, int]:
    return _convert_padding_back(cget(self, (int,), "-padding"))


def set_padding(self, value: int | tuple[int, ...] | None) -> None:
    config(self, padding=_convert_padding(value))


padding = property(get_padding, set_padding)
