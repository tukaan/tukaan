from __future__ import annotations

import contextlib
from math import cos, radians, sin, tan
from typing import TYPE_CHECKING, Any

from tukaan._tcl import Tcl
from tukaan._utils import flatten, seq_pairs
from tukaan.colors import Color
from tukaan.fonts.font import Font

from .canvas import Canvas
from .equipment import Brush, Pen
from .utils import ArrowHead, DashPattern
from .transform import Transform, matmul

if TYPE_CHECKING:
    from PIL.Image import Image

    from tukaan._images import Icon


def get_arrowhead_options(start, end) -> dict[str, str | float]:
    result = {}

    if start is not None:
        result.update(start._get_startarrow())
    if end is not None:
        result.update(end._get_endarrow())

    return result


def get_font_options_for_text_item(font) -> tuple:
    if isinstance(font, Font):
        font_dict = font._get_props()
    elif isinstance(font, tuple):
        font_dict = dict(seq_pairs(font))
    else:
        return ()

    family = font_dict.get("-family", "Helvetica")
    size = font_dict.get("-size", 12)
    weight = font_dict.get("-weight", "normal")
    slant = font_dict.get("-slant", "normal")
    if slant == "roman":
        slant = "normal"

    return Tcl.to_tcl_args(
        fontfamily=family,
        fontsize=size,
        fontweight=weight,
        fontslant=slant,
    )


class CanvasItem:
    _name: str
    _options: dict[str, Any] | None = None
    _matrix = None

    def __init__(self, parent: Canvas | Group) -> None:
        self._options = {}

        self.parent = parent
        self.canvas = canvas = parent
        if isinstance(parent, Canvas):
            self.canvas = canvas = parent
        else:
            self.canvas = canvas = parent.canvas
            self._options["parent"] = parent

    def transform(self, transform: Transform):
        self._matrix = matrix = matmul(transform._matrix, self._matrix)

        Tcl.call(None, self.canvas, "itemconfigure", self, "-matrix", matrix)

    def reset_transform(self):
        Tcl.call(None, self.canvas, "itemconfigure", self, "-matrix", ((1, 0), (0, 1), (0, 0)))

    def _store_options(self, **kwargs) -> None:
        self._options.update(kwargs)

    def _get_options(self) -> None:
        options = list(Tcl.to_tcl_args(**self._options))

        with contextlib.suppress(AttributeError):
            options.extend(self._brush.__to_tcl__())

        with contextlib.suppress(AttributeError):
            options.extend(self._pen.__to_tcl__())

        return tuple(options)


class FilledObject:
    def _store_brush(self, brush: Brush | None) -> None:
        self._brush = brush or self.canvas.brush

    @property
    def brush(self):
        opacity = Tcl.call(float, self.canvas, "itemcget", self, "-fillopacity")
        fillrule = Tcl.call(str, self.canvas, "itemcget", self, "-fillrule")
        fill = Tcl.call(str, self.canvas, "itemcget", self, "-fill")

        if fill in Tcl.call([str], self.canvas, "gradient", "names"):
            fill = self.canvas._gradient_superclass.__from_tcl__(fill)
        else:
            fill = Color.__from_tcl__(fill)

        return Brush(fill=fill, opacity=opacity, fillrule=fillrule)

    @brush.setter
    def brush(self, new_brush: Brush | None) -> None:
        if new_brush is not None:
            options = new_brush.__to_tcl__()
        else:
            options = ("-fill", "", "-fillopacity", "1.0", "-fillrule", "nonzero")
        Tcl.call(None, self.canvas, "itemconfigure", self, *options)


class OutlinedObject:
    def _store_pen(self, pen: Pen | None):
        self._pen = pen or self.canvas.pen

    @property
    def pen(self) -> Pen:
        color = Tcl.call(Color, self.canvas, "itemcget", self, "-stroke")
        width = Tcl.call(float, self.canvas, "itemcget", self, "-strokewidth")
        # pattern = Tcl.call(DashPattern, self.canvas, "itemcget", self, "-strokedasharray")  # can cause segfaults
        line_cap = Tcl.call(str, self.canvas, "itemcget", self, "-strokelinecap")
        line_join = Tcl.call(str, self.canvas, "itemcget", self, "-strokelinejoin")

        return Pen(
            color=color,
            width=width,
            pattern=None,
            line_cap=line_cap,
            line_join=line_join,
        )

    @pen.setter
    def pen(self, new_pen: Pen | None) -> None:
        if new_brush is not None:
            options = new_brush.__to_tcl__()
        else:
            options = ("-fill", "", "-fillopacity", "1.0", "-fillrule", "nonzero")
        Tcl.call(None, self.canvas, "itemconfigure", self, *options)


class Group(CanvasItem):
    def __init__(self, parent: Canvas | Group) -> None:
        super().__init__(parent)
        self._name = Tcl.call(str, self.canvas, "create", "group")

    def move(self, x, y) -> None:
        Tcl.call(None, self.canvas, "move", self, x, y)


class Line(CanvasItem, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        *,
        pen: Pen | None = None,
        startarrow: ArrowHead | None = None,
        endarrow: ArrowHead | None = None,
    ):
        super().__init__(parent)

        self._store_pen(pen)
        self._store_options(**get_arrowhead_options(startarrow, endarrow))

    def draw(
        self, start: tuple[float, float] = (0, 0), end: tuple[float, float] = (20, 20)
    ) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "pline",
            *start,
            *end,
            *self._get_options(),
        )


class Vector(CanvasItem, OutlinedObject):
    # FIXME:
    # I know it's not good that the line that connects two points is called "Line",
    # and the line with angle and length is called "Vector"
    # If you have some better ideas, please HELP!

    def __init__(
        self,
        parent: Canvas | Group,
        length: float,
        angle: float = 0,
        *,
        pen: Pen | None = None,
        startarrow: ArrowHead | None = None,
        endarrow: ArrowHead | None = None,
    ):
        super().__init__(parent)

        self._angle = angle
        self._length = length

        self._store_pen(pen)
        self._store_options(**get_arrowhead_options(startarrow, endarrow))

    def draw(self, x: float = 0, y: float = 0) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "pline",
            x,
            y,
            *self._get_x_y(x, y),
            *self._get_options(),
        )

    def _get_x_y(self, x, y) -> tuple[float, float]:
        angle = self._angle
        length = self._length

        if angle > 360 or angle < 0:
            raise ValueError("angle must be between 0 and 360")

        return x + cos(radians(angle)) * length, y - sin(radians(angle)) * length


class PolygonalLine(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        *,
        brush: Brush | None = None,
        pen: Pen | None = None,
        startarrow: ArrowHead | None = None,
        endarrow: ArrowHead | None = None,
    ):
        super().__init__(parent)

        self._store_brush(brush)
        self._store_pen(pen)
        self._store_options(**get_arrowhead_options(startarrow, endarrow))

    def draw(self, *coords) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "polyline",
            *flatten(coords),
            *self._get_options(),
        )


class Polygon(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        *,
        brush: Brush | None = None,
        pen: Pen | None = None,
    ):
        super().__init__(parent)

        self._store_brush(brush)
        self._store_pen(pen)

    def draw(self, *coords) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "ppolygon",
            *flatten(coords),
            *self._get_options(),
        )


class Rectangle(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        width: float,
        height: float,
        *,
        border_radius: float | tuple[float, float] | None = None,
        brush: Brush | None = None,
        pen: Pen | None = None,
    ) -> None:

        super().__init__(parent)

        if isinstance(border_radius, (tuple, list)):
            rx = ry = border_radius
        else:
            rx = ry = border_radius

        self._store_brush(brush)
        self._store_pen(pen)
        self._store_options(rx=rx, ry=ry)
        self._w = width
        self._h = height

    def draw(self, x: float = 0, y: float = 0) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "prect",
            x,
            y,
            x + self._w,
            y + self._h,
            *self._get_options(),
        )


class Square(Rectangle, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        sides: float,
        *,
        border_radius: float | tuple[float, float] | None = None,
        brush: Brush | None = None,
        pen: Pen | None = None,
    ) -> None:
        Rectangle.__init__(
            self, parent, sides, sides, border_radius=border_radius, brush=brush, pen=pen
        )


class Ellipse(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        radius: tuple[float, float],
        *,
        brush: Brush | None = None,
        pen: Pen | None = None,
    ) -> None:
        super().__init__(parent)

        if not isinstance(radius, tuple) or len(radius) != 2:
            raise TypeError("radius must be a tuple of two values")

        rx, ry = radius

        self._store_options(rx=rx, ry=ry)
        self._store_brush(brush)
        self._store_pen(pen)

    def draw(self, x: int = 0, y: int = 0) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "ellipse",
            x,
            y,
            *self._get_options(),
        )


class Circle(Ellipse, FilledObject, OutlinedObject):
    # TkPath has a circle element, but it's simpler to just inherit ellipse
    def __init__(
        self,
        parent: Canvas | Group,
        radius: float | None = None,
        *,
        brush: Brush | None = None,
        pen: Pen | None = None,
    ) -> None:
        Ellipse.__init__(self, parent, (radius, radius), brush=brush, pen=pen)


class Path(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        draw: str,
        *,
        brush: Brush | None = None,
        pen: Pen | None = None,
        startarrow: ArrowHead | None = None,
        endarrow: ArrowHead | None = None,
    ):
        super().__init__(parent)

        self._draw = draw

        self._store_brush(brush)
        self._store_pen(pen)
        self._store_options(**get_arrowhead_options(startarrow, endarrow))

    def draw(self) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "path",
            self._draw.replace(",", ""),
            *self._get_options(),
        )


class Text(CanvasItem, FilledObject, OutlinedObject):
    def __init__(
        self,
        parent: Canvas | Group,
        text: str | None = None,
        *,
        anchor: str | None = "nw",  # TODO: use enum
        brush: Brush | None = None,
        stroke_under_fill: bool = True,
        font: Font | None = None,
        pen: Pen | None = None,
    ) -> None:
        super().__init__(parent)

        self._font_props = get_font_options_for_text_item(font)

        self._store_brush(brush)
        self._store_pen(pen)
        self._store_options(text=text, filloverstroke=stroke_under_fill, textanchor=anchor)

    def draw(self, x: float = 0, y: float = 0) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "ptext",
            x,
            y,
            *self._get_options(),
            *self._font_props,
        )


class Image(CanvasItem):
    def __init__(
        self,
        parent: Canvas | Group,
        image: Image | Icon | None = None,
        *,
        width: float | None = None,
        height: float | None = None,
        tint: Color | str | None = None,
        tint_amount: float | None = None,
    ):
        super().__init__(parent)

        self._store_options(
            image=image,
            height=height,
            width=width,
            tintcolor=tint,
            tintamount=tint_amount,
        )

    def draw(self, x: float = 0, y: float = 0) -> None:
        self._name = Tcl.call(
            str,
            self.canvas,
            "create",
            "pimage",
            x,
            y,
            *self._get_options(),
        )
